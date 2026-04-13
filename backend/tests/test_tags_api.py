from __future__ import annotations

import pytest

from backend.app.models import Tag
from backend.tests.support import create_initialized_test_client


def test_create_tag_success() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.post(
            "/api/tags",
            json={"name": "重要", "color": "#FF0000"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["name"] == "重要"
    assert payload["data"]["color"] == "#FF0000"
    assert "id" in payload["data"]


def test_create_tag_with_default_color() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.post(
            "/api/tags",
            json={"name": "普通"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["color"] == "#409EFF"


def test_create_tag_rejects_duplicate_name() -> None:
    with create_initialized_test_client() as (client, _, _):
        client.post("/api/tags", json={"name": "重要"})
        response = client.post("/api/tags", json={"name": "重要"})

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "tag_already_exists"


def test_list_tags_returns_all_tags() -> None:
    with create_initialized_test_client() as (client, _, _):
        client.post("/api/tags", json={"name": "重要", "color": "#FF0000"})
        client.post("/api/tags", json={"name": "紧急", "color": "#FFA500"})

        response = client.get("/api/tags")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]) == 2
    tag_names = {tag["name"] for tag in payload["data"]}
    assert tag_names == {"重要", "紧急"}


def test_update_tag_name() -> None:
    with create_initialized_test_client() as (client, _, _):
        create_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = create_response.json()["data"]["id"]

        response = client.put(f"/api/tags/{tag_id}", json={"name": "非常重要"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["name"] == "非常重要"


def test_update_tag_color() -> None:
    with create_initialized_test_client() as (client, _, _):
        create_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = create_response.json()["data"]["id"]

        response = client.put(f"/api/tags/{tag_id}", json={"color": "#00FF00"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["color"] == "#00FF00"


def test_update_tag_rejects_duplicate_name() -> None:
    with create_initialized_test_client() as (client, _, _):
        client.post("/api/tags", json={"name": "重要"})
        create_response = client.post("/api/tags", json={"name": "紧急"})
        tag_id = create_response.json()["data"]["id"]

        response = client.put(f"/api/tags/{tag_id}", json={"name": "重要"})

    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "tag_name_conflict"


def test_update_tag_returns_not_found_for_missing_tag() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.put("/api/tags/999", json={"name": "新名称"})

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "tag_not_found"


def test_delete_tag_success() -> None:
    with create_initialized_test_client() as (client, _, _):
        create_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = create_response.json()["data"]["id"]

        response = client.delete(f"/api/tags/{tag_id}")

    assert response.status_code == 200
    assert response.json()["success"] is True

    list_response = client.get("/api/tags")
    assert len(list_response.json()["data"]) == 0


def test_delete_tag_returns_not_found_for_missing_tag() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.delete("/api/tags/999")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "tag_not_found"


def test_delete_tag_cascades_to_document_relations(monkeypatch: pytest.MonkeyPatch) -> None:
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

    with create_initialized_test_client() as (client, _, _):
        tag_response = client.post("/api/tags", json={"name": "重要"})
        tag_id = tag_response.json()["data"]["id"]

        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("demo.txt", b"document body", "text/plain")},
        )
        document_id = upload_response.json()["data"]["document_id"]

        client.post(f"/api/documents/{document_id}/tags", json={"tag_id": tag_id})

        response = client.delete(f"/api/tags/{tag_id}")

        assert response.status_code == 200

        tags_response = client.get(f"/api/documents/{document_id}/tags")
        assert len(tags_response.json()["data"]) == 0
