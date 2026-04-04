from __future__ import annotations

from redis import Redis


def create_redis_client(redis_url: str) -> Redis:
    return Redis.from_url(redis_url)


def check_redis_connection(redis_client: Redis) -> bool:
    return bool(redis_client.ping())
