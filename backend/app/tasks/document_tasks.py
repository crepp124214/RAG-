from __future__ import annotations

import logging

from backend.app.orchestrators.document_ingestion import DocumentIngestionOrchestrator
from backend.app.models import Document, Task
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.app.services.visual_asset_service import PdfVisualAssetService
from backend.app.tasks.graph_tasks import enqueue_graph_build
from backend.app.settings import get_backend_settings
from backend.infrastructure.database import create_database_engine, create_session_factory
from backend.infrastructure.llm import create_embedding_client, create_vision_caption_client
from backend.infrastructure.observability import log_event
from backend.infrastructure.queue import DEFAULT_QUEUE_NAME, create_queue, create_redis_client, enqueue_callable


logger = logging.getLogger(__name__)


def enqueue_document_ingestion(document_id: str, task_id: str) -> dict[str, str | int]:
    settings = get_backend_settings()
    engine = create_database_engine(settings.database_url)

    log_event(
        logger,
        logging.INFO,
        'worker.document_task_started',
        document_id=document_id,
        task_id=task_id,
    )

    try:
        session_factory = create_session_factory(engine)
        orchestrator = DocumentIngestionOrchestrator(
            session_factory=session_factory,
            parser_service=DocumentParserService(),
            chunking_service=DocumentChunkingService(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            ),
            embedding_client=create_embedding_client(settings),
            visual_asset_service=PdfVisualAssetService(),
            vision_caption_client=create_vision_caption_client(settings),
            multimodal_enabled=settings.multimodal_enabled,
            max_visual_assets_per_document=settings.max_visual_assets_per_document,
        )
        result = orchestrator.process(document_id=document_id, task_id=task_id)
        graph_task_id = _schedule_graph_build(session_factory, settings, document_id)
        log_event(
            logger,
            logging.INFO,
            'worker.document_task_finished',
            document_id=document_id,
            task_id=task_id,
            status=result['status'],
            graph_task_id=graph_task_id,
        )
        return result
    finally:
        engine.dispose()


def _schedule_graph_build(session_factory, settings, document_id: str) -> str:
    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        if document is None:
            raise RuntimeError("document not found for graph build")
        document.graph_status = "NOT_STARTED"
        graph_task = Task(document_id=document_id, task_type="GRAPH_BUILD", status="UPLOADED")
        db_session.add_all([document, graph_task])
        db_session.commit()
        db_session.refresh(graph_task)
        graph_task_id = graph_task.id

    redis_client = create_redis_client(settings.redis_url)
    queue = create_queue(redis_client, queue_name=DEFAULT_QUEUE_NAME)
    try:
        enqueue_callable(queue, enqueue_graph_build, document_id, graph_task_id)
    except Exception as exc:
        with session_factory() as db_session:
            document = db_session.get(Document, document_id)
            graph_task = db_session.get(Task, graph_task_id)
            if document is not None:
                document.graph_status = "FAILED"
                document.graph_relation_count = 0
                db_session.add(document)
            if graph_task is not None:
                graph_task.status = "FAILED"
                graph_task.error_message = str(exc)[:2000]
                db_session.add(graph_task)
            db_session.commit()
        log_event(
            logger,
            logging.WARNING,
            "worker.graph_task_enqueue_failed",
            document_id=document_id,
            graph_task_id=graph_task_id,
            error_message=str(exc),
        )
    return graph_task_id
