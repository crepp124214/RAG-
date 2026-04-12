from __future__ import annotations

import importlib
import json
import logging
from typing import Any

import pytest
from rq.timeouts import TimerDeathPenalty

from backend.infrastructure.queue.queue import DEFAULT_QUEUE_NAME
worker_main = importlib.import_module("worker.main")


class FakeRedisClient:
    pass


def _log_payloads(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [json.loads(record.message) for record in caplog.records]


def test_create_worker_subscribes_to_target_queues(monkeypatch: pytest.MonkeyPatch) -> None:
    created_queues: list[str] = []
    constructed: dict[str, Any] = {}

    class FakeQueue:
        def __init__(self, queue_name: str) -> None:
            self.name = queue_name

    def fake_create_queue(redis_client: FakeRedisClient, *, queue_name: str, is_async: bool = True) -> FakeQueue:
        assert is_async is True
        created_queues.append(queue_name)
        return FakeQueue(queue_name)

    class FakeWorker:
        def __init__(self, *, queues: list[FakeQueue], connection: FakeRedisClient) -> None:
            constructed["queues"] = queues
            constructed["connection"] = connection

    fake_redis = FakeRedisClient()
    monkeypatch.setattr(worker_main, "create_queue", fake_create_queue)
    monkeypatch.setattr(worker_main, "resolve_worker_class", lambda: FakeWorker)

    worker = worker_main.create_worker(fake_redis, queue_names=["documents", "system"])

    assert isinstance(worker, FakeWorker)
    assert created_queues == ["documents", "system"]
    assert [queue.name for queue in constructed["queues"]] == ["documents", "system"]
    assert constructed["connection"] is fake_redis


def test_create_worker_uses_default_queue_name(monkeypatch: pytest.MonkeyPatch) -> None:
    created_queues: list[str] = []

    def fake_create_queue(redis_client: FakeRedisClient, *, queue_name: str, is_async: bool = True) -> object:
        created_queues.append(queue_name)
        return object()

    class FakeWorker:
        def __init__(self, *, queues: list[object], connection: FakeRedisClient) -> None:
            self.queues = queues
            self.connection = connection

    monkeypatch.setattr(worker_main, "create_queue", fake_create_queue)
    monkeypatch.setattr(worker_main, "resolve_worker_class", lambda: FakeWorker)

    worker_main.create_worker(FakeRedisClient())

    assert created_queues == [DEFAULT_QUEUE_NAME]


def test_resolve_worker_class_uses_windows_simple_worker_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker_main.os, "name", "nt")

    assert worker_main.resolve_worker_class() is worker_main.WindowsSimpleWorker
    assert worker_main.WindowsSimpleWorker.death_penalty_class is TimerDeathPenalty


def test_resolve_worker_class_uses_default_worker_on_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(worker_main.os, "name", "posix")

    assert worker_main.resolve_worker_class() is worker_main.Worker


def test_main_emits_worker_lifecycle_logs_for_success(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    worked: list[bool] = []

    class FakeQueue:
        def __init__(self, name: str) -> None:
            self.name = name

    class FakeWorker:
        def __init__(self) -> None:
            self.queues = [FakeQueue("documents")]

        def work(self) -> None:
            worked.append(True)

    monkeypatch.setattr(
        worker_main,
        "get_backend_settings",
        lambda: type("Settings", (), {"redis_url": "redis://127.0.0.1:6379/0"})(),
    )
    monkeypatch.setattr(worker_main, "create_redis_client", lambda redis_url: FakeRedisClient())
    monkeypatch.setattr(worker_main, "check_redis_connection", lambda redis_client: True)
    monkeypatch.setattr(worker_main, "create_worker", lambda redis_client, queue_names=None: FakeWorker())

    with caplog.at_level(logging.INFO):
        worker_main.main()

    payloads = _log_payloads(caplog)

    assert worked == [True]
    assert payloads[0]["event"] == "worker.startup_started"
    assert payloads[0]["queue_names"] == [DEFAULT_QUEUE_NAME]
    assert payloads[0]["redis_host"] == "127.0.0.1"
    assert payloads[0]["redis_port"] == 6379
    assert payloads[1]["event"] == "worker.redis_connection_succeeded"
    assert payloads[2] == {
        "event": "worker.configured",
        "worker_class": "FakeWorker",
        "queue_names": ["documents"],
    }
    assert payloads[3] == {
        "event": "worker.run_completed",
        "worker_class": "FakeWorker",
        "queue_names": ["documents"],
    }


def test_main_logs_redis_connectivity_failure_context(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        worker_main,
        "get_backend_settings",
        lambda: type("Settings", (), {"redis_url": "redis://127.0.0.1:6379/5"})(),
    )
    monkeypatch.setattr(worker_main, "create_redis_client", lambda redis_url: FakeRedisClient())

    def fail_check(redis_client: FakeRedisClient) -> bool:
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(worker_main, "check_redis_connection", fail_check)

    with pytest.raises(RuntimeError, match="redis unavailable"):
        with caplog.at_level(logging.INFO):
            worker_main.main()

    payloads = _log_payloads(caplog)

    assert payloads[0]["event"] == "worker.startup_started"
    assert payloads[1]["event"] == "worker.redis_connection_failed"
    assert payloads[1]["error"] == "redis unavailable"
    assert payloads[1]["error_type"] == "RuntimeError"
    assert payloads[1]["redis_db"] == "5"
    assert payloads[2]["event"] == "worker.run_failed"
    assert payloads[2]["stage"] == "redis_connect"
    assert payloads[2]["error"] == "redis unavailable"


def test_main_logs_terminal_worker_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeQueue:
        def __init__(self, name: str) -> None:
            self.name = name

    class FakeWorker:
        def __init__(self) -> None:
            self.queues = [FakeQueue("documents"), FakeQueue("system")]

        def work(self) -> None:
            raise RuntimeError("worker crashed")

    monkeypatch.setattr(
        worker_main,
        "get_backend_settings",
        lambda: type("Settings", (), {"redis_url": "redis://localhost:6380/0"})(),
    )
    monkeypatch.setattr(worker_main, "create_redis_client", lambda redis_url: FakeRedisClient())
    monkeypatch.setattr(worker_main, "check_redis_connection", lambda redis_client: True)
    monkeypatch.setattr(worker_main, "create_worker", lambda redis_client, queue_names=None: FakeWorker())

    with pytest.raises(RuntimeError, match="worker crashed"):
        with caplog.at_level(logging.INFO):
            worker_main.main()

    payloads = _log_payloads(caplog)

    assert payloads[2] == {
        "event": "worker.configured",
        "worker_class": "FakeWorker",
        "queue_names": ["documents", "system"],
    }
    assert payloads[3]["event"] == "worker.run_failed"
    assert payloads[3]["stage"] == "work"
    assert payloads[3]["worker_class"] == "FakeWorker"
    assert payloads[3]["queue_names"] == ["documents", "system"]
    assert payloads[3]["error"] == "worker crashed"
