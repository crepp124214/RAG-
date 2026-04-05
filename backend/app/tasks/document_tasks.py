from __future__ import annotations

import logging

from backend.app.orchestrators.document_ingestion import DocumentIngestionOrchestrator
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.app.settings import get_backend_settings
from backend.infrastructure.database import create_database_engine, create_session_factory
from backend.infrastructure.llm import create_embedding_client
from backend.infrastructure.observability import log_event


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
        )
        result = orchestrator.process(document_id=document_id, task_id=task_id)
        log_event(
            logger,
            logging.INFO,
            'worker.document_task_finished',
            document_id=document_id,
            task_id=task_id,
            status=result['status'],
        )
        return result
    finally:
        engine.dispose()
