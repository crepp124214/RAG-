from __future__ import annotations

import logging
import os
from collections.abc import Sequence
from urllib.parse import urlparse

from redis import Redis
from rq import Queue, SimpleWorker, Worker
from rq.timeouts import TimerDeathPenalty

from backend.app.settings import get_backend_settings
from backend.infrastructure.observability import log_event
from backend.infrastructure.queue import (
    DEFAULT_QUEUE_NAME,
    check_redis_connection,
    create_redis_client,
    create_queue,
)


logger = logging.getLogger(__name__)


class WindowsSimpleWorker(SimpleWorker):
    """Windows 环境使用线程计时器超时控制，避免依赖 SIGALRM。"""

    death_penalty_class = TimerDeathPenalty


def resolve_worker_class() -> type[Worker]:
    """Windows 环境使用无 fork 的 worker，其余平台沿用默认 Worker。"""
    if os.name == "nt":
        return WindowsSimpleWorker
    return Worker


def create_worker(
    redis_client: Redis,
    *,
    queue_names: Sequence[str] | None = None,
) -> Worker:
    resolved_queue_names = list(queue_names or [DEFAULT_QUEUE_NAME])
    queues = [
        create_queue(
            redis_client,
            queue_name=queue_name,
        )
        for queue_name in resolved_queue_names
    ]
    worker_class = resolve_worker_class()
    return worker_class(
        queues=queues,
        connection=redis_client,
    )


def _resolve_queue_names(queue_names: Sequence[str] | None = None) -> list[str]:
    return list(queue_names or [DEFAULT_QUEUE_NAME])


def _extract_redis_log_fields(redis_url: str) -> dict[str, str | int | None]:
    parsed = urlparse(redis_url)
    redis_db = parsed.path.lstrip("/") or None
    return {
        "redis_host": parsed.hostname,
        "redis_port": parsed.port,
        "redis_db": redis_db,
    }


def _worker_queue_names(worker: Worker, fallback_queue_names: Sequence[str]) -> list[str]:
    queues = getattr(worker, "queues", None)
    if not queues:
        return list(fallback_queue_names)

    resolved_names: list[str] = []
    for queue in queues:
        queue_name = getattr(queue, "name", None)
        if isinstance(queue_name, str) and queue_name:
            resolved_names.append(queue_name)

    return resolved_names or list(fallback_queue_names)


def main() -> None:
    settings = get_backend_settings()
    queue_names = _resolve_queue_names()
    redis_fields = _extract_redis_log_fields(settings.redis_url)
    worker: Worker | None = None
    stage = "redis_connect"

    log_event(
        logger,
        logging.INFO,
        "worker.startup_started",
        queue_names=queue_names,
        **redis_fields,
    )

    try:
        redis_client = create_redis_client(settings.redis_url)
        check_redis_connection(redis_client)
        log_event(
            logger,
            logging.INFO,
            "worker.redis_connection_succeeded",
            queue_names=queue_names,
            **redis_fields,
        )
    except Exception as exc:
        log_event(
            logger,
            logging.ERROR,
            "worker.redis_connection_failed",
            queue_names=queue_names,
            error=str(exc),
            error_type=type(exc).__name__,
            **redis_fields,
        )
        log_event(
            logger,
            logging.ERROR,
            "worker.run_failed",
            stage=stage,
            error=str(exc),
        )
        raise

    try:
        stage = "configure"
        worker = create_worker(redis_client, queue_names=queue_names)
        worker_queue_names = _worker_queue_names(worker, queue_names)
        worker_class = type(worker).__name__
        log_event(
            logger,
            logging.INFO,
            "worker.configured",
            worker_class=worker_class,
            queue_names=worker_queue_names,
        )

        stage = "work"
        worker.work()
        log_event(
            logger,
            logging.INFO,
            "worker.run_completed",
            worker_class=worker_class,
            queue_names=worker_queue_names,
        )
    except Exception as exc:
        failure_fields: dict[str, object] = {
            "stage": stage,
            "error": str(exc),
        }
        if worker is not None:
            failure_fields["worker_class"] = type(worker).__name__
            failure_fields["queue_names"] = _worker_queue_names(worker, queue_names)
        log_event(
            logger,
            logging.ERROR,
            "worker.run_failed",
            **failure_fields,
        )
        raise


if __name__ == "__main__":
    main()
