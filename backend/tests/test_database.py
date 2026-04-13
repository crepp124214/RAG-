from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy import inspect, select

from backend.app.models import Chunk, Document, Message, Session, Task
from backend.infrastructure.database.connection import check_database_connection, create_database_engine
from backend.infrastructure.database.initializer import initialize_database
from backend.infrastructure.database.session import create_session_factory


def create_workspace_temp_dir() -> Path:
    temp_dir = Path("backend/tests/.tmp") / str(uuid4())
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_alembic_scaffold_exists_for_phase_one_schema() -> None:
    assert Path("alembic.ini").exists()
    assert Path(
        "backend/infrastructure/database/migrations/env.py",
    ).exists()
    assert Path(
        "backend/infrastructure/database/migrations/versions/20260403_000001_create_phase_one_tables.py",
    ).exists()


def test_create_database_engine_and_health_check_support_sqlite() -> None:
    database_file = create_workspace_temp_dir() / "database.sqlite3"
    engine = create_database_engine(f"sqlite+pysqlite:///{database_file}")

    assert Path(str(engine.url.database)).resolve() == database_file.resolve()
    assert check_database_connection(engine) is True


def test_initialize_database_creates_phase_one_tables() -> None:
    database_file = create_workspace_temp_dir() / "schema.sqlite3"
    engine = create_database_engine(f"sqlite+pysqlite:///{database_file}")

    initialize_database(engine)

    inspector = inspect(engine)
    assert set(inspector.get_table_names()) == {
        "documents",
        "tasks",
        "sessions",
        "messages",
        "chunks",
        "document_tags",
        "document_tag_relations",
    }


def test_initialize_database_creates_chunk_embedding_column() -> None:
    database_file = create_workspace_temp_dir() / "vector_schema.sqlite3"
    engine = create_database_engine(f"sqlite+pysqlite:///{database_file}")

    initialize_database(engine)

    inspector = inspect(engine)
    chunk_columns = {column["name"] for column in inspector.get_columns("chunks")}

    assert "embedding" in chunk_columns


def test_phase_one_models_support_minimal_insert_and_query() -> None:
    database_file = create_workspace_temp_dir() / "records.sqlite3"
    engine = create_database_engine(f"sqlite+pysqlite:///{database_file}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name="示例文档",
            file_type="pdf",
            status="UPLOADED",
            storage_path="/tmp/demo.pdf",
        )
        db_session.add(document)
        db_session.flush()

        task = Task(
            document_id=document.id,
            task_type="INGESTION",
            status="UPLOADED",
        )
        session = Session(title="第一条问题自动生成的标题")
        db_session.add_all([task, session])
        db_session.flush()

        message = Message(
            session_id=session.id,
            role="user",
            content="这是一条测试消息",
        )
        chunk = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="这是一段测试分块内容",
            source_type="text",
            page_number=1,
        )
        db_session.add_all([message, chunk])
        db_session.commit()

    with session_factory() as db_session:
        stored_document = db_session.scalar(select(Document))
        stored_task = db_session.scalar(select(Task))
        stored_session = db_session.scalar(select(Session))
        stored_message = db_session.scalar(select(Message))
        stored_chunk = db_session.scalar(select(Chunk))

    assert stored_document is not None
    assert stored_document.name == "示例文档"
    assert stored_task is not None
    assert stored_task.document_id == stored_document.id
    assert stored_session is not None
    assert stored_session.title == "第一条问题自动生成的标题"
    assert stored_message is not None
    assert stored_message.role == "user"
    assert stored_chunk is not None
    assert stored_chunk.page_number == 1
