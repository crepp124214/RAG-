from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from backend.app.models import Document, Task
from backend.app.tasks.document_tasks import enqueue_document_ingestion
from backend.app.services import document_service as document_service_module
from backend.infrastructure.storage.file_storage import build_storage_path
from backend.tests.support import create_initialized_test_client


def patch_document_queue(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        document_service_module,
        "create_redis_client",
        lambda redis_url: {"redis_url": redis_url},
    )
    monkeypatch.setattr(
        document_service_module,
        "create_queue",
        lambda redis_client, queue_name=document_service_module.DEFAULT_QUEUE_NAME: {
            "redis_client": redis_client,
            "queue_name": queue_name,
        },
    )

    def fake_enqueue(queue: object, func: object, *args: object) -> object:
        captured["queue"] = queue
        captured["func"] = func
        captured["args"] = args
        return type("Job", (), {"id": "job-123"})()

    monkeypatch.setattr(document_service_module, "enqueue_callable", fake_enqueue)
    return captured


@pytest.mark.parametrize(
    ("filename", "content", "expected_file_type"),
    [
        ("demo.txt", b"hello world", "txt"),
        ("report.pdf", b"%PDF-1.4 minimal", "pdf"),
        ("notes.docx", b"PK\x03\x04 minimal", "docx"),
    ],
)
def test_upload_document_creates_records_and_enqueues_job(
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    content: bytes,
    expected_file_type: str,
) -> None:
    captured = patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, settings):
        response = client.post(
            "/api/documents/upload",
            files={"file": (filename, content, "application/octet-stream")},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True

        document_id = payload["data"]["document_id"]
        task_id = payload["data"]["task_id"]

        with client.app.state.db_session_factory() as db_session:
            stored_document = db_session.get(Document, document_id)
            stored_task = db_session.get(Task, task_id)

        expected_path, _ = build_storage_path(settings.file_storage_path, filename, content)

    assert stored_document is not None
    assert stored_document.name == filename
    assert stored_document.file_type == expected_file_type
    assert stored_document.status == "UPLOADED"
    assert stored_document.storage_path == str(expected_path)
    assert Path(stored_document.storage_path).exists()

    assert stored_task is not None
    assert stored_task.document_id == document_id
    assert stored_task.task_type == "INGESTION"
    assert stored_task.status == "UPLOADED"

    assert captured["func"] is enqueue_document_ingestion
    assert captured["args"] == (document_id, task_id)


def test_upload_document_rejects_duplicate_content(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        first = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"same content", "text/plain")},
        )
        second = client.post(
            "/api/documents/upload",
            files={"file": ("copy.txt", b"same content", "text/plain")},
        )

    assert first.status_code == 200
    assert second.status_code == 409
    payload = second.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "document_already_exists"


@pytest.mark.parametrize(
    ("filename", "content", "expected_code"),
    [
        ("demo.txt", b"", "empty_file"),
        ("demo.exe", b"hello", "unsupported_file_type"),
    ],
)
def test_upload_document_rejects_invalid_file_input(
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    content: bytes,
    expected_code: str,
) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        response = client.post(
            "/api/documents/upload",
            files={"file": (filename, content, "application/octet-stream")},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == expected_code


def test_get_document_returns_expected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        response = client.get(f"/api/documents/{document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == document_id
    assert payload["data"]["name"] == "demo.txt"
    assert payload["data"]["status"] == "UPLOADED"
    assert isinstance(payload["data"]["created_at"], str)
    assert isinstance(payload["data"]["updated_at"], str)


def test_get_task_returns_expected_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        task_id = upload_response.json()["data"]["task_id"]

        response = client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == task_id
    assert payload["data"]["task_type"] == "INGESTION"
    assert payload["data"]["status"] == "UPLOADED"
    assert payload["data"]["error_message"] is None
    assert isinstance(payload["data"]["created_at"], str)
    assert isinstance(payload["data"]["updated_at"], str)


def test_get_document_returns_not_found_for_missing_document() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get("/api/documents/missing-document")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "document_not_found"


def test_get_task_returns_not_found_for_missing_task() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get("/api/tasks/missing-task")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "task_not_found"


def test_delete_document_removes_database_records_and_source_file(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]
        task_id = upload_response.json()["data"]["task_id"]

        document_response = client.get(f"/api/documents/{document_id}")
        storage_path = Path(document_response.json()["data"]["storage_path"])

        response = client.delete(f"/api/documents/{document_id}")

        with client.app.state.db_session_factory() as db_session:
            stored_document = db_session.get(Document, document_id)
            stored_task = db_session.get(Task, task_id)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert stored_document is None
    assert stored_task is None
    assert not storage_path.exists()


def test_delete_document_returns_not_found_when_document_is_missing() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.delete("/api/documents/missing-document")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "document_not_found"


def test_upload_rolls_back_when_enqueue_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(document_service_module, "create_redis_client", lambda redis_url: object())
    monkeypatch.setattr(
        document_service_module,
        "create_queue",
        lambda redis_client, queue_name=document_service_module.DEFAULT_QUEUE_NAME: object(),
    )

    def raise_enqueue_error(queue: object, func: object, *args: object) -> None:
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(document_service_module, "enqueue_callable", raise_enqueue_error)

    with create_initialized_test_client() as (client, _, _):
        response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )

        with client.app.state.db_session_factory() as db_session:
            document_count = len(db_session.scalars(select(Document)).all())
            task_count = len(db_session.scalars(select(Task)).all())

    assert response.status_code == 500
    assert document_count == 0
    assert task_count == 0
