from __future__ import annotations

from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.settings.config import BackendSettings, load_backend_settings
from backend.infrastructure.database.initializer import initialize_database
from backend.main import create_app


def create_workspace_temp_dir(prefix: str = "test") -> Path:
    temp_dir = Path("backend/tests/.tmp") / f"{prefix}-{uuid4()}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def build_test_settings(temp_dir: Path, overrides: Mapping[str, str] | None = None) -> BackendSettings:
    base_overrides: dict[str, str] = {
        "APP_ENV": "test",
        "APP_NAME": "RAG测试应用",
        "DATABASE_URL": f"sqlite+pysqlite:///{(temp_dir / 'app.sqlite3').resolve()}",
        "REDIS_URL": "redis://127.0.0.1:6379/0",
        "DASHSCOPE_API_KEY": "test-key",
        "FILE_STORAGE_PATH": str((temp_dir / "uploads").resolve()),
    }
    if overrides:
        base_overrides.update(overrides)
    return load_backend_settings(env_file=None, overrides=base_overrides)


@contextmanager
def create_initialized_test_client(
    *,
    overrides: Mapping[str, str] | None = None,
    raise_server_exceptions: bool = False,
) -> Generator[tuple[TestClient, Path, BackendSettings], None, None]:
    temp_dir = create_workspace_temp_dir()
    settings = build_test_settings(temp_dir, overrides=overrides)
    app = create_app(settings)

    with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
        initialize_database(client.app.state.db_engine)
        yield client, temp_dir, settings
