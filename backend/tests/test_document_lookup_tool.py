from __future__ import annotations

from backend.app.models import Chunk, Document, Task
from backend.app.tools.document_lookup import DocumentLookupTool
from backend.infrastructure.database import create_database_engine, create_session_factory, initialize_database
from backend.tests.support import create_workspace_temp_dir


def test_document_lookup_returns_document_status() -> None:
    temp_dir = create_workspace_temp_dir("document-lookup")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'lookup.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    tool = DocumentLookupTool()

    with session_factory() as db_session:
        document = Document(
            name="demo.txt",
            file_type="txt",
            status="READY",
            storage_path="/tmp/demo.txt",
        )
        db_session.add(document)
        db_session.commit()

        result = tool.execute(
            db_session,
            {"lookup_type": "status", "document_id": document.id},
        )

    engine.dispose()

    assert result.record.status == "success"
    assert result.output["document"]["id"] == document.id
    assert result.output["document"]["status"] == "READY"


def test_document_lookup_returns_task_status() -> None:
    temp_dir = create_workspace_temp_dir("task-lookup")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'lookup.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    tool = DocumentLookupTool()

    with session_factory() as db_session:
        document = Document(
            name="demo.txt",
            file_type="txt",
            status="PARSING",
            storage_path="/tmp/demo.txt",
        )
        db_session.add(document)
        db_session.flush()
        task = Task(
            document_id=document.id,
            task_type="ingestion",
            status="FAILED",
            error_message="bad file",
        )
        db_session.add(task)
        db_session.commit()

        result = tool.execute(
            db_session,
            {"lookup_type": "status", "task_id": task.id},
        )

    engine.dispose()

    assert result.record.status == "success"
    assert result.output["task"]["id"] == task.id
    assert result.output["task"]["status"] == "FAILED"
    assert result.output["task"]["error_message"] == "bad file"


def test_document_lookup_returns_content_matches() -> None:
    temp_dir = create_workspace_temp_dir("content-lookup")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'lookup.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    tool = DocumentLookupTool()

    with session_factory() as db_session:
        document = Document(
            name="manual.txt",
            file_type="txt",
            status="READY",
            storage_path="/tmp/manual.txt",
        )
        db_session.add(document)
        db_session.flush()
        db_session.add_all(
            [
                Chunk(
                    document_id=document.id,
                    chunk_index=0,
                    content="系统今天已经完成验收。",
                    source_type="text",
                    page_number=1,
                ),
                Chunk(
                    document_id=document.id,
                    chunk_index=1,
                    content="这里是无关内容。",
                    source_type="text",
                    page_number=2,
                ),
            ]
        )
        db_session.commit()

        result = tool.execute(
            db_session,
            {"lookup_type": "content", "document_id": document.id, "query": "今天 验收"},
        )

    engine.dispose()

    assert result.record.status == "success"
    assert result.output["matches"][0]["document_name"] == "manual.txt"
    assert result.output["matches"][0]["page_number"] == 1
    assert "今天已经完成验收" in result.output["matches"][0]["content"]
