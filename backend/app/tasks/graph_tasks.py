from __future__ import annotations

import logging

from sqlalchemy import select

from backend.app.exceptions import AppError
from backend.app.models import Chunk, Document, Task
from backend.app.services.graph_service import GraphTripleExtractionService
from backend.app.settings import get_backend_settings
from backend.infrastructure.database import create_database_engine, create_session_factory
from backend.infrastructure.graph import create_graph_store
from backend.infrastructure.llm.factory import create_graph_extractor_client
from backend.infrastructure.observability import log_event


logger = logging.getLogger(__name__)


def enqueue_graph_build(document_id: str, task_id: str) -> dict[str, str | int]:
    settings = get_backend_settings()
    engine = create_database_engine(settings.database_url)

    try:
        session_factory = create_session_factory(engine)
        graph_store = create_graph_store(settings)
        extractor_service = GraphTripleExtractionService(
            extractor_client=create_graph_extractor_client(settings)
        )

        with session_factory() as db_session:
            document = db_session.get(Document, document_id)
            task = db_session.get(Task, task_id)
            if document is None or task is None:
                raise RuntimeError("graph task target missing")

            task.status = "PROCESSING"
            task.error_message = None
            document.graph_status = "PROCESSING"
            db_session.add_all([document, task])
            db_session.commit()

            triples = []
            chunks = db_session.scalars(
                select(Chunk).where(Chunk.document_id == document_id).where(Chunk.source_type == "text")
            ).all()
            for chunk in chunks:
                try:
                    triples.extend(
                        extractor_service.extract_from_chunk(
                            chunk_id=chunk.id,
                            document_id=document_id,
                            page_number=chunk.page_number,
                            content=chunk.content,
                        )
                    )
                except Exception as exc:
                    if isinstance(exc, AppError):
                        raise
                    log_event(logger, logging.WARNING, "graph.chunk_extraction_failed", document_id=document_id, chunk_id=chunk.id, error_message=str(exc))

            relation_count = graph_store.write_document_graph(document_id=document_id, triples=triples)
            document.graph_status = "READY"
            document.graph_relation_count = relation_count
            task.status = "READY"
            task.error_message = None
            db_session.add_all([document, task])
            db_session.commit()

            return {"document_id": document_id, "task_id": task_id, "status": "READY", "relation_count": relation_count}
    except Exception as exc:
        with create_session_factory(engine)() as db_session:
            document = db_session.get(Document, document_id)
            task = db_session.get(Task, task_id)
            if document is not None:
                document.graph_status = "FAILED"
                document.graph_relation_count = 0
                db_session.add(document)
            if task is not None:
                task.status = "FAILED"
                task.error_message = str(exc)[:2000]
                db_session.add(task)
            db_session.commit()
        raise
    finally:
        engine.dispose()
