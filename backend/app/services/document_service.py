from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.models import Chunk, Document, Task
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.settings import BackendSettings
from backend.app.tasks.document_tasks import enqueue_document_ingestion
from backend.infrastructure.graph import create_graph_store
from backend.infrastructure.observability import log_event
from backend.infrastructure.queue import (
    DEFAULT_QUEUE_NAME,
    create_queue,
    create_redis_client,
    enqueue_callable,
)
from backend.infrastructure.storage.file_storage import persist_upload_file


logger = logging.getLogger(__name__)


def create_document_upload(
    db_session: Session,
    *,
    settings: BackendSettings,
    filename: str | None,
    content: bytes,
) -> tuple[Document, Task]:
    stored_file = persist_upload_file(
        settings.file_storage_path,
        filename,
        content,
        settings.max_upload_size_mb,
    )

    document_repository = DocumentRepository(db_session)
    task_repository = TaskRepository(db_session)

    existing_document = document_repository.get_by_storage_path(str(stored_file.storage_path))
    if existing_document is not None:
        raise AppError("文件已存在", code="document_already_exists", status_code=409)

    document = document_repository.add(
        Document(
            name=stored_file.original_name,
            file_type=stored_file.file_type,
            status="UPLOADED",
            storage_path=str(stored_file.storage_path),
        )
    )
    task = task_repository.add(
        Task(
            document_id=document.id,
            task_type="INGESTION",
            status="UPLOADED",
        )
    )

    db_session.commit()
    db_session.refresh(document)
    db_session.refresh(task)

    try:
        redis_client = create_redis_client(settings.redis_url)
        queue = create_queue(redis_client, queue_name=DEFAULT_QUEUE_NAME)
        enqueue_callable(
            queue,
            enqueue_document_ingestion,
            document.id,
            task.id,
        )
    except Exception:
        persisted_document = document_repository.get_by_id(document.id)
        if persisted_document is not None:
            db_session.delete(persisted_document)
            db_session.commit()

        if stored_file.storage_path.exists():
            stored_file.storage_path.unlink()

        raise

    log_event(
        logger,
        logging.INFO,
        "document.upload_enqueued",
        document_id=document.id,
        task_id=task.id,
        file_type=document.file_type,
        storage_path=document.storage_path,
    )

    return document, task


def get_document_detail(db_session: Session, document_id: str) -> tuple[Document, int]:
    document = DocumentRepository(db_session).get_by_id(document_id)
    if document is None:
        raise AppError("文档不存在", code="document_not_found", status_code=404)
    statement = (
        select(func.count(Chunk.id))
        .where(Chunk.document_id == document_id)
        .where(Chunk.source_type != "text")
    )
    visual_asset_count = int(db_session.scalar(statement) or 0)
    return document, visual_asset_count


def get_task_detail(db_session: Session, task_id: str) -> Task:
    task = TaskRepository(db_session).get_by_id(task_id)
    if task is None:
        raise AppError("任务不存在", code="task_not_found", status_code=404)
    return task


def delete_document(db_session: Session, document_id: str, *, settings: BackendSettings | None = None) -> None:
    document = DocumentRepository(db_session).get_by_id(document_id)
    if document is None:
        raise AppError("文档不存在", code="document_not_found", status_code=404)

    storage_path = document.storage_path
    if settings is not None:
        try:
            create_graph_store(settings).delete_document_graph(document_id=document_id)
        except Exception as exc:
            log_event(
                logger,
                logging.WARNING,
                "document.graph_cleanup_failed",
                document_id=document_id,
                error=str(exc),
            )
    db_session.delete(document)
    db_session.commit()

    file_path = Path(storage_path)
    if file_path.exists():
        file_path.unlink()
    asset_dir = file_path.parent / f"{file_path.stem}_assets"
    if asset_dir.exists():
        for child in asset_dir.iterdir():
            if child.is_file():
                child.unlink()
        asset_dir.rmdir()

    log_event(
        logger,
        logging.INFO,
        "document.deleted",
        document_id=document_id,
        storage_path=storage_path,
    )
