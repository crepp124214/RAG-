from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from backend.app.models import Chunk, Document, Task
from backend.app.orchestrators.document_ingestion import DocumentIngestionOrchestrator
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.infrastructure.database import create_database_engine, create_session_factory, initialize_database
from backend.tests.support import create_workspace_temp_dir


class FakeEmbeddingClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.fail:
            raise RuntimeError("embedding unavailable")
        return [[0.1, 0.2, 0.3] for _ in texts]


def create_document_with_task(session_factory, storage_path: Path) -> tuple[str, str]:
    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="txt",
            status="UPLOADED",
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.flush()

        task = Task(
            document_id=document.id,
            task_type="INGESTION",
            status="UPLOADED",
        )
        db_session.add(task)
        db_session.commit()
        return document.id, task.id


def test_document_ingestion_processes_document_to_ready() -> None:
    temp_dir = create_workspace_temp_dir("ingestion")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("第一段。\n第二段。\n第三段。", encoding="utf-8")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'ingestion.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = create_document_with_task(session_factory, storage_path)

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=DocumentParserService(),
        chunking_service=DocumentChunkingService(chunk_size=12, chunk_overlap=2),
        embedding_client=FakeEmbeddingClient(),
    )

    result = orchestrator.process(document_id=document_id, task_id=task_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)
        chunks = db_session.scalars(select(Chunk).order_by(Chunk.chunk_index)).all()

    engine.dispose()

    assert result["status"] == "READY"
    assert document is not None and document.status == "READY"
    assert task is not None and task.status == "READY"
    assert task.error_message is None
    assert len(chunks) >= 1
    assert all(chunk.embedding is not None for chunk in chunks)


def test_document_ingestion_marks_document_and_task_failed_on_error() -> None:
    temp_dir = create_workspace_temp_dir("ingestion")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("第一段。\n第二段。", encoding="utf-8")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'failure.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = create_document_with_task(session_factory, storage_path)

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=DocumentParserService(),
        chunking_service=DocumentChunkingService(chunk_size=12, chunk_overlap=2),
        embedding_client=FakeEmbeddingClient(fail=True),
    )

    with pytest.raises(RuntimeError):
        orchestrator.process(document_id=document_id, task_id=task_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)

    engine.dispose()

    assert document is not None and document.status == "FAILED"
    assert task is not None and task.status == "FAILED"
    assert task.error_message == "embedding unavailable"
