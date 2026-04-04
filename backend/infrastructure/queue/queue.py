from __future__ import annotations

from collections.abc import Callable
from typing import Any

from redis import Redis
from rq import Queue
from rq.job import Job


DEFAULT_QUEUE_NAME = "document_ingestion"


def create_queue(
    redis_client: Redis,
    *,
    queue_name: str = DEFAULT_QUEUE_NAME,
    is_async: bool = True,
) -> Queue:
    return Queue(
        name=queue_name,
        connection=redis_client,
        is_async=is_async,
    )


def enqueue_callable(
    queue: Queue,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Job:
    return queue.enqueue(func, *args, **kwargs)
