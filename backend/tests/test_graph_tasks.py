from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.models import Chunk, Document, Task
from backend.app.tasks import document_tasks as document_tasks_module
from backend.app.tasks import graph_tasks as graph_tasks_module
from backend.infrastructure.database import create_database_engine, create_session_factory, initialize_database
from backend.tests.support import create_workspace_temp_dir, build_test_settings


class FakeGraphStore:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.writes: list[tuple[str, list[object]]] = []

    def write_document_graph(self, *, document_id: str, triples: list[object]) -> int:
        if self.fail:
            raise RuntimeError("neo4j unavailable")
        self.writes.append((document_id, triples))
        return len(triples)

    def delete_document_graph(self, *, document_id: str) -> None:
        del document_id


class FakeExtractorClient:
    def extract_triples(self, *, text: str) -> list[dict[str, object]]:
        del text
        return [{"subject": "平台A", "predicate": "依赖", "object": "服务B", "entity_type": "system"}]


def _seed_document_with_graph_task(session_factory, storage_path: Path) -> tuple[str, str]:
    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="txt",
            status="READY",
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.flush()

        chunk = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="平台A依赖服务B。",
            source_type="text",
            page_number=1,
        )
        ingestion_task = Task(document_id=document.id, task_type="INGESTION", status="READY")
        graph_task = Task(document_id=document.id, task_type="GRAPH_BUILD", status="UPLOADED")
        db_session.add_all([chunk, ingestion_task, graph_task])
        db_session.commit()
        return document.id, graph_task.id


def test_enqueue_graph_build_updates_document_summary_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = create_workspace_temp_dir("graph-task")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("平台A依赖服务B。", encoding="utf-8")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'graph.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = _seed_document_with_graph_task(session_factory, storage_path)

    fake_store = FakeGraphStore()
    monkeypatch.setattr(graph_tasks_module, "create_graph_store", lambda settings: fake_store)
    monkeypatch.setattr(graph_tasks_module, "create_graph_extractor_client", lambda settings: FakeExtractorClient())
    monkeypatch.setattr(graph_tasks_module, "create_database_engine", lambda database_url: engine)
    monkeypatch.setattr(
        graph_tasks_module,
        "get_backend_settings",
        lambda: build_test_settings(temp_dir, overrides={"DATABASE_URL": f"sqlite+pysqlite:///{(temp_dir / 'graph.sqlite3').resolve()}"}),
    )

    result = graph_tasks_module.enqueue_graph_build(document_id, task_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)

    engine.dispose()

    assert result["status"] == "READY"
    assert document is not None and document.status == "READY"
    assert document is not None and document.graph_status == "READY"
    assert document is not None and document.graph_relation_count == 1
    assert task is not None and task.status == "READY"
    assert fake_store.writes


def test_enqueue_graph_build_marks_graph_summary_failed_without_breaking_document_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    temp_dir = create_workspace_temp_dir("graph-task-fail")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("平台A依赖服务B。", encoding="utf-8")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'graph-fail.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = _seed_document_with_graph_task(session_factory, storage_path)

    monkeypatch.setattr(graph_tasks_module, "create_graph_store", lambda settings: FakeGraphStore(fail=True))
    monkeypatch.setattr(graph_tasks_module, "create_graph_extractor_client", lambda settings: FakeExtractorClient())
    monkeypatch.setattr(graph_tasks_module, "create_database_engine", lambda database_url: engine)
    monkeypatch.setattr(
        graph_tasks_module,
        "get_backend_settings",
        lambda: build_test_settings(temp_dir, overrides={"DATABASE_URL": f"sqlite+pysqlite:///{(temp_dir / 'graph-fail.sqlite3').resolve()}"}),
    )

    with pytest.raises(RuntimeError):
        graph_tasks_module.enqueue_graph_build(document_id, task_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)

    engine.dispose()

    assert document is not None and document.status == "READY"
    assert document is not None and document.graph_status == "FAILED"
    assert document is not None and document.graph_relation_count == 0
    assert task is not None and task.status == "FAILED"
    assert task is not None and task.error_message == "neo4j unavailable"


def test_schedule_graph_build_marks_graph_failed_when_enqueue_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = create_workspace_temp_dir("graph-schedule-fail")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("平台A依赖服务B。", encoding="utf-8")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'graph-schedule.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="txt",
            status="READY",
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.commit()
        document_id = document.id

    monkeypatch.setattr(document_tasks_module, "create_redis_client", lambda redis_url: object())
    monkeypatch.setattr(document_tasks_module, "create_queue", lambda redis_client, queue_name: object())

    def fail_enqueue(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(document_tasks_module, "enqueue_callable", fail_enqueue)
    settings = build_test_settings(
        temp_dir,
        overrides={"DATABASE_URL": f"sqlite+pysqlite:///{(temp_dir / 'graph-schedule.sqlite3').resolve()}"},
    )

    graph_task_id = document_tasks_module._schedule_graph_build(session_factory, settings, document_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        graph_task = db_session.get(Task, graph_task_id)

    engine.dispose()

    assert document is not None and document.status == "READY"
    assert document is not None and document.graph_status == "FAILED"
    assert graph_task is not None and graph_task.status == "FAILED"
    assert graph_task is not None and graph_task.error_message == "redis unavailable"
