from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, text


def _build_connect_args(database_url: str) -> dict[str, Any]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def create_database_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        future=True,
        pool_pre_ping=True,
        connect_args=_build_connect_args(database_url),
    )


def check_database_connection(engine: Engine) -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
