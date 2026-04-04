from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.exceptions import AppError
from backend.app.settings.config import load_backend_settings
from backend.main import create_app


def build_test_client() -> TestClient:
    app = create_app(
        load_backend_settings(
            env_file=None,
            overrides={
                "APP_ENV": "test",
                "APP_NAME": "RAG测试应用",
                "DATABASE_URL": "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/rag_assistant",
                "REDIS_URL": "redis://127.0.0.1:6379/0",
                "DASHSCOPE_API_KEY": "test-key",
                "FILE_STORAGE_PATH": "./data/uploads",
            },
        )
    )

    @app.get("/api/test/app-error")
    async def raise_app_error() -> None:
        raise AppError("业务校验失败", code="app_error", status_code=409)

    @app.get("/api/test/system-error")
    async def raise_system_error() -> None:
        raise RuntimeError("unexpected")

    return TestClient(app, raise_server_exceptions=False)


def test_health_check_returns_success_payload() -> None:
    client = build_test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["app_env"] == "test"


def test_missing_route_returns_standard_error_response() -> None:
    client = build_test_client()

    response = client.get("/api/not-found")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "not_found"


def test_docs_page_is_available() -> None:
    client = build_test_client()

    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_app_error_uses_standard_error_shape() -> None:
    client = build_test_client()

    response = client.get("/api/test/app-error")

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "app_error"
    assert payload["error"]["detail"] == "业务校验失败"


def test_unhandled_error_is_converted_to_standard_error_response() -> None:
    client = build_test_client()

    response = client.get("/api/test/system-error")

    assert response.status_code == 500
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "internal_server_error"
