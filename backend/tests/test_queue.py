from __future__ import annotations

from typing import Any

import pytest

from backend.app.tasks.system_tasks import run_failure_task, run_success_task
from backend.infrastructure.queue.connection import check_redis_connection, create_redis_client
from backend.infrastructure.queue.queue import DEFAULT_QUEUE_NAME, create_queue, enqueue_callable


class FakeRedisClient:
    def __init__(self, *, should_ping: bool = True) -> None:
        self.should_ping = should_ping

    def ping(self) -> bool:
        return self.should_ping


def test_create_redis_client_uses_configured_url(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, Any] = {}

    class FakeRedisModule:
        @staticmethod
        def from_url(redis_url: str) -> FakeRedisClient:
            created["redis_url"] = redis_url
            return FakeRedisClient()

    monkeypatch.setattr(
        "backend.infrastructure.queue.connection.Redis",
        FakeRedisModule,
    )

    redis_client = create_redis_client("redis://127.0.0.1:6379/0")

    assert created["redis_url"] == "redis://127.0.0.1:6379/0"
    assert isinstance(redis_client, FakeRedisClient)


def test_check_redis_connection_returns_true_on_ping() -> None:
    assert check_redis_connection(FakeRedisClient()) is True


def test_check_redis_connection_propagates_ping_failures() -> None:
    class BrokenRedisClient:
        def ping(self) -> bool:
            raise RuntimeError("redis unavailable")

    with pytest.raises(RuntimeError, match="redis unavailable"):
        check_redis_connection(BrokenRedisClient())  # type: ignore[arg-type]


def test_create_queue_binds_queue_name_and_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    class FakeQueue:
        def __init__(self, *, name: str, connection: FakeRedisClient, is_async: bool) -> None:
            captured["name"] = name
            captured["connection"] = connection
            captured["is_async"] = is_async

    fake_redis = FakeRedisClient()
    monkeypatch.setattr("backend.infrastructure.queue.queue.Queue", FakeQueue)

    queue = create_queue(fake_redis, queue_name=DEFAULT_QUEUE_NAME, is_async=False)

    assert isinstance(queue, FakeQueue)
    assert captured["name"] == DEFAULT_QUEUE_NAME
    assert captured["connection"] is fake_redis
    assert captured["is_async"] is False


def test_enqueue_callable_forwards_job_arguments() -> None:
    captured: dict[str, Any] = {}

    class FakeJob:
        id = "job-1"

    class FakeQueue:
        def enqueue(self, func: Any, *args: Any, **kwargs: Any) -> FakeJob:
            captured["func"] = func
            captured["args"] = args
            captured["kwargs"] = kwargs
            return FakeJob()

    job = enqueue_callable(
        FakeQueue(),  # type: ignore[arg-type]
        run_success_task,
        {"value": "hello"},
        job_timeout=300,
    )

    assert job.id == "job-1"
    assert captured["func"] is run_success_task
    assert captured["args"] == ({"value": "hello"},)
    assert captured["kwargs"]["job_timeout"] == 300


def test_system_success_task_returns_expected_payload() -> None:
    assert run_success_task({"value": "demo"}) == {
        "status": "ok",
        "value": "demo",
    }


def test_system_failure_task_raises_readable_error() -> None:
    with pytest.raises(RuntimeError, match="boom"):
        run_failure_task("boom")
