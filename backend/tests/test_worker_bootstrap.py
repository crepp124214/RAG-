from __future__ import annotations

from typing import Any
import importlib

import pytest
from rq.timeouts import TimerDeathPenalty

from backend.infrastructure.queue.queue import DEFAULT_QUEUE_NAME
worker_main = importlib.import_module("worker.main")


class FakeRedisClient:
    pass


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
