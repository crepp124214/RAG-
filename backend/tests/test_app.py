from __future__ import annotations

from backend.app.exceptions import AppError
from backend.tests.support import create_initialized_test_client


def test_health_check_returns_success_payload() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["app_env"] == "test"


def test_missing_route_returns_standard_error_response() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get("/api/not-found")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "not_found"


def test_docs_page_is_available() -> None:
    with create_initialized_test_client() as (client, _, _):
        response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_app_error_uses_standard_error_shape() -> None:
    with create_initialized_test_client() as (client, _, _):
        @client.app.get("/api/test/app-error")
        async def raise_app_error() -> None:
            raise AppError("业务校验失败", code="app_error", status_code=409)

        response = client.get("/api/test/app-error")

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "app_error"
    assert payload["error"]["detail"] == "业务校验失败"


def test_unhandled_error_is_converted_to_standard_error_response() -> None:
    with create_initialized_test_client() as (client, _, _):
        @client.app.get("/api/test/system-error")
        async def raise_system_error() -> None:
            raise RuntimeError("unexpected")

        response = client.get("/api/test/system-error")

    assert response.status_code == 500
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "internal_server_error"
