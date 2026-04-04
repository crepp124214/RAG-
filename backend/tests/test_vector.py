from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from backend.app.models import Chunk, Document
from backend.infrastructure.database.connection import create_database_engine
from backend.infrastructure.database.initializer import initialize_database
from backend.infrastructure.database.session import create_session_factory
from backend.infrastructure.vector.store import search_similar_chunks, update_chunk_embedding


def create_workspace_temp_dir() -> Path:
    temp_dir = Path("backend/tests/.tmp") / str(uuid4())
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_vector_store_supports_embedding_write_and_similarity_search_on_sqlite() -> None:
    database_file = create_workspace_temp_dir() / "vector_records.sqlite3"
    engine = create_database_engine(f"sqlite+pysqlite:///{database_file}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name="vector-demo.txt",
            file_type="txt",
            status="READY",
            storage_path="/tmp/vector-demo.txt",
        )
        db_session.add(document)
        db_session.flush()

        chunk_one = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="第一段分块内容",
            source_type="text",
            page_number=1,
        )
        chunk_two = Chunk(
            document_id=document.id,
            chunk_index=1,
            content="第二段分块内容",
            source_type="text",
            page_number=2,
        )
        db_session.add_all([chunk_one, chunk_two])
        db_session.flush()

        update_chunk_embedding(db_session, chunk_one.id, [1.0, 0.0, 0.0])
        update_chunk_embedding(db_session, chunk_two.id, [0.0, 1.0, 0.0])
        db_session.commit()

    with session_factory() as db_session:
        stored_chunks = db_session.scalars(select(Chunk).order_by(Chunk.chunk_index)).all()
        results = search_similar_chunks(
            db_session,
            [0.9, 0.1, 0.0],
            limit=2,
        )

    assert stored_chunks[0].embedding == [1.0, 0.0, 0.0]
    assert stored_chunks[1].embedding == [0.0, 1.0, 0.0]
    assert [result.chunk_id for result in results] == [stored_chunks[0].id, stored_chunks[1].id]
    assert results[0].score > results[1].score


def test_vector_store_returns_empty_results_for_empty_dataset() -> None:
    database_file = create_workspace_temp_dir() / "vector_empty.sqlite3"
    engine = create_database_engine(f"sqlite+pysqlite:///{database_file}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        results = search_similar_chunks(
            db_session,
            [1.0, 0.0, 0.0],
            limit=3,
        )

    assert results == []
