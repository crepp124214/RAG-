from __future__ import annotations

import logging

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from backend.app.exceptions import AppError
from backend.app.models import Chunk, Document, Task
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.infrastructure.observability import log_event
from backend.infrastructure.vector.store import ensure_vector_extension, update_chunk_embedding


logger = logging.getLogger(__name__)


class DocumentIngestionOrchestrator:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        parser_service: DocumentParserService,
        chunking_service: DocumentChunkingService,
        embedding_client: object,
    ) -> None:
        self.session_factory = session_factory
        self.parser_service = parser_service
        self.chunking_service = chunking_service
        self.embedding_client = embedding_client

    def process(self, *, document_id: str, task_id: str) -> dict[str, str | int]:
        with self.session_factory() as db_session:
            document = db_session.get(Document, document_id)
            task = db_session.get(Task, task_id)
            if document is None:
                raise AppError("文档不存在", code="document_not_found", status_code=404)
            if task is None:
                raise AppError("任务不存在", code="task_not_found", status_code=404)

            log_event(
                logger,
                logging.INFO,
                "document.ingestion_started",
                document_id=document.id,
                task_id=task.id,
            )

            try:
                self._set_status(db_session, document=document, task=task, status="PARSING")
                parsed_documents = self.parser_service.parse_file(
                    document.storage_path,
                    file_type=document.file_type,
                    original_name=document.name,
                )
                if not parsed_documents:
                    raise AppError("文档解析结果为空", code="document_parse_empty", status_code=400)

                self._set_status(db_session, document=document, task=task, status="CHUNKING")
                chunk_payloads = self.chunking_service.split_documents(
                    parsed_documents,
                    document_id=document.id,
                    source_type="text",
                )
                if not chunk_payloads:
                    raise AppError("文档分块结果为空", code="document_chunk_empty", status_code=400)

                self._set_status(db_session, document=document, task=task, status="EMBEDDING")
                embeddings = self.embedding_client.embed_texts(
                    [payload.content for payload in chunk_payloads]
                )
                if len(embeddings) != len(chunk_payloads):
                    raise AppError("向量化结果数量不匹配", code="embedding_result_mismatch", status_code=502)

                self._replace_chunks(
                    db_session,
                    document=document,
                    chunk_payloads=chunk_payloads,
                    embeddings=embeddings,
                )

                document.status = "READY"
                task.status = "READY"
                task.error_message = None
                db_session.add_all([document, task])
                db_session.commit()

                log_event(
                    logger,
                    logging.INFO,
                    "document.ingestion_completed",
                    document_id=document.id,
                    task_id=task.id,
                    chunk_count=len(chunk_payloads),
                )

                return {
                    "document_id": document.id,
                    "task_id": task.id,
                    "status": "READY",
                    "chunk_count": len(chunk_payloads),
                }
            except Exception as exc:
                db_session.rollback()
                self._mark_failed(db_session, document=document, task=task, error_message=str(exc))
                log_event(
                    logger,
                    logging.ERROR,
                    "document.ingestion_failed",
                    document_id=document.id,
                    task_id=task.id,
                    error_message=str(exc),
                )
                raise

    def _replace_chunks(
        self,
        db_session: Session,
        *,
        document: Document,
        chunk_payloads: list,
        embeddings: list[list[float]],
    ) -> None:
        ensure_vector_extension(db_session)
        db_session.execute(delete(Chunk).where(Chunk.document_id == document.id))
        db_session.flush()

        for payload, embedding in zip(chunk_payloads, embeddings, strict=True):
            chunk = Chunk(
                document_id=document.id,
                chunk_index=payload.chunk_index,
                content=payload.content,
                source_type=payload.source_type,
                page_number=payload.page_number,
            )
            db_session.add(chunk)
            db_session.flush()
            update_chunk_embedding(db_session, chunk.id, embedding)

        db_session.commit()

    def _set_status(
        self,
        db_session: Session,
        *,
        document: Document,
        task: Task,
        status: str,
    ) -> None:
        document.status = status
        task.status = status
        task.error_message = None
        db_session.add_all([document, task])
        db_session.commit()
        log_event(
            logger,
            logging.INFO,
            "document.status_changed",
            document_id=document.id,
            task_id=task.id,
            status=status,
        )

    def _mark_failed(
        self,
        db_session: Session,
        *,
        document: Document,
        task: Task,
        error_message: str,
    ) -> None:
        document.status = "FAILED"
        task.status = "FAILED"
        task.error_message = error_message[:2000]
        db_session.add_all([document, task])
        db_session.commit()
