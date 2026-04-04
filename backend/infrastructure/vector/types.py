from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


def normalize_embedding(value: list[float] | tuple[float, ...] | None) -> list[float] | None:
    if value is None:
        return None

    normalized = [float(item) for item in value]
    if not normalized:
        raise ValueError("embedding must not be empty")
    return normalized


class EmbeddingVector(TypeDecorator[list[float] | None]):
    """Use pgvector on PostgreSQL and JSON on lightweight test databases."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector())
        return dialect.type_descriptor(JSON())

    def process_bind_param(
        self,
        value: list[float] | tuple[float, ...] | None,
        dialect: Any,
    ) -> list[float] | None:
        return normalize_embedding(value)

    def process_result_value(
        self,
        value: list[float] | None,
        dialect: Any,
    ) -> list[float] | None:
        return normalize_embedding(value)
