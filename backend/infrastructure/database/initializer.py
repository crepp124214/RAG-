from __future__ import annotations

from sqlalchemy import Engine, text

from backend.app.models import Base


def initialize_database(engine: Engine) -> None:
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
