from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from backend.app.exceptions import AppError


def get_db_session(request: Request) -> Generator[Session, None, None]:
    session_factory = getattr(request.app.state, "db_session_factory", None)
    if session_factory is None:
        raise AppError("数据库会话工厂未初始化", code="database_not_ready", status_code=500)

    session = session_factory()
    try:
        yield session
    finally:
        session.close()
