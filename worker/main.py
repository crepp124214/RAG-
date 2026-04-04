from __future__ import annotations

from collections.abc import Sequence

from redis import Redis
from rq import Queue, Worker

from backend.app.settings import get_backend_settings
from backend.infrastructure.queue import (
    DEFAULT_QUEUE_NAME,
    check_redis_connection,
    create_redis_client,
    create_queue,
)


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
    return Worker(
        queues=queues,
        connection=redis_client,
    )


def main() -> None:
    settings = get_backend_settings()
    redis_client = create_redis_client(settings.redis_url)
    check_redis_connection(redis_client)
    worker = create_worker(redis_client)
    worker.work()


if __name__ == "__main__":
    main()
