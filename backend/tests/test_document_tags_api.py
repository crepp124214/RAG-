from __future__ import annotations

import pytest

from backend.tests.support import create_initialized_test_client


def patch_document_queue(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.app.services import document_service as document_service_module

    monkeypatch.setattr(document_service_module, "create_redis_client", lambda redis_url: object())
    monkeypatch.setattr(
        document_service_module,
        "create_queue",
        lambda redis_client, queue_name=document_service_module.DEFAULT_QUEUE_NAME: object(),
    )
    monkeypatch.setattr(
        document_service_module,
        "enqueue_callable",
        lambda queue, func, *args: type("Job", (), {"id": "job-123"})(),
    )


def test_add_document_tag_success(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        tag_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = tag_response.json()["data"]["id"]

        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        response = client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag_id})

        assert response.status_code == 200
        assert response.json()["success"] is True


def test_add_document_tag_rejects_duplicate(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        tag_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = tag_response.json()["data"]["id"]

        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag_id})
        response = client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag_id})

        assert response.status_code == 409
        payload = response.json()
        assert payload["error"]["code"] == "tag_already_added"


def test_remove_document_tag_success(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        tag_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = tag_response.json()["data"]["id"]

        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag_id})
        response = client.delete(f"/api/documents/{document_id}/tags/{tag_id}")

        assert response.status_code == 200
        assert response.json()["success"] is True


def test_set_document_tags_replaces_all_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        tag1_response = client.post("/api/tags", json={"name": "重要"})
        tag1_id = tag1_response.json()["data"]["id"]

        tag2_response = client.post("/api/tags", json={"name": "紧急"})
        tag2_id = tag2_response.json()["data"]["id"]

        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag1_id})

        response = client.put(f"/api/documents/{document_id}/tags", json={"tag_ids": [tag2_id]})

        assert response.status_code == 200

        tags_response = client.get(f"/api/documents/{document_id}/tags")
        tags = tags_response.json()["data"]
        assert len(tags) == 1
        assert tags[0]["id"] == tag2_id


def test_list_document_tags_returns_all_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        tag1_response = client.post("/api/tags", json={"name": "重要"})
        tag1_id = tag1_response.json()["data"]["id"]

        tag2_response = client.post("/api/tags", json={"name": "紧急"})
        tag2_id = tag2_response.json()["data"]["id"]

        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag1_id})
        client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag2_id})

        response = client.get(f"/api/documents/{document_id}/tags")

        assert response.status_code == 200
        tags = response.json()["data"]
        assert len(tags) == 2
        tag_names = {tag["name"] for tag in tags}
        assert tag_names == {"重要", "紧急"}


def test_list_documents_with_search(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        client.post("/api/documents/upload", files={"file": ("report.txt", b"content", "text/plain")})
        client.post("/api/documents/upload", files={"file": ("notes.txt", b"content2", "text/plain")})
        client.post("/api/documents/upload", files={"file": ("summary.txt", b"content3", "text/plain")})

        response = client.get("/api/documents?search=report")

        assert response.status_code == 200
        documents = response.json()["data"]
        assert len(documents) == 1
        assert documents[0]["name"] == "report.txt"


def test_list_documents_with_tag_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        tag_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = tag_response.json()["data"]["id"]

        upload1 = client.post("/api/documents/upload", files={"file": ("doc1.txt", b"content", "text/plain")})
        doc1_id = upload1.json()["data"]["document_id"]

        upload2 = client.post("/api/documents/upload", files={"file": ("doc2.txt", b"content2", "text/plain")})
        doc2_id = upload2.json()["data"]["document_id"]

        client.post(f"/api/documents/{doc1_id}/tags", json={"tag_id": tag_id})

        response = client.get(f"/api/documents?tags={tag_id}")

        assert response.status_code == 200
        documents = response.json()["data"]
        assert len(documents) == 1
        assert documents[0]["id"] == doc1_id


def test_batch_upload_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        response = client.post(
            "/api/documents/batch-upload",
            files=[
                ("files", ("doc1.txt", b"content1", "text/plain")),
                ("files", ("doc2.txt", b"content2", "text/plain")),
            ],
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert len(payload["data"]) == 2


def test_batch_delete_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        upload1 = client.post("/api/documents/upload", files={"file": ("doc1.txt", b"content", "text/plain")})
        doc1_id = upload1.json()["data"]["document_id"]

        upload2 = client.post("/api/documents/upload", files={"file": ("doc2.txt", b"content2", "text/plain")})
        doc2_id = upload2.json()["data"]["document_id"]

        response = client.post("/api/documents/batch-delete", json={"document_ids": [doc1_id, doc2_id]})

        assert response.status_code == 200
        assert response.json()["success"] is True

        doc1_response = client.get(f"/api/documents/{doc1_id}")
        assert doc1_response.status_code == 404

        doc2_response = client.get(f"/api/documents/{doc2_id}")
        assert doc2_response.status_code == 404


def test_batch_tag_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        tag_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = tag_response.json()["data"]["id"]

        upload1 = client.post("/api/documents/upload", files={"file": ("doc1.txt", b"content", "text/plain")})
        doc1_id = upload1.json()["data"]["document_id"]

        upload2 = client.post("/api/documents/upload", files={"file": ("doc2.txt", b"content2", "text/plain")})
        doc2_id = upload2.json()["data"]["document_id"]

        response = client.post(
            "/api/documents/batch-tag",
            json={"document_ids": [doc1_id, doc2_id], "tag_ids": [tag_id]},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        doc1_tags = client.get(f"/api/documents/{doc1_id}/tags").json()["data"]
        assert len(doc1_tags) == 1
        assert doc1_tags[0]["id"] == tag_id

        doc2_tags = client.get(f"/api/documents/{doc2_id}/tags").json()["data"]
        assert len(doc2_tags) == 1
        assert doc2_tags[0]["id"] == tag_id


def test_document_preview_returns_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        from backend.app.models import Chunk

        with client.app.state.db_session_factory() as db_session:
            for i in range(10):
                chunk = Chunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=f"Chunk {i} content",
                    source_type="text",
                    page_number=1,
                )
                db_session.add(chunk)
            db_session.commit()

        response = client.get(f"/api/documents/{document_id}/preview?limit=3")

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert len(payload["data"]) == 3
        assert payload["data"][0]["chunk_index"] == 0
        assert payload["data"][0]["content"] == "Chunk 0 content"
