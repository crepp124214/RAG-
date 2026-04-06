from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from sqlalchemy import Float, select, text
from sqlalchemy.orm import Session

from backend.app.models import Chunk
from backend.infrastructure.vector.types import normalize_embedding


@dataclass(slots=True)
class ChunkSimilarityResult:
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    page_number: int | None
    source_type: str
    asset_label: str | None
    preview_available: bool
    score: float


def ensure_vector_extension(db_session: Session) -> None:
    if db_session.bind is None or db_session.bind.dialect.name != "postgresql":
        return

    db_session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


def update_chunk_embedding(
    db_session: Session,
    chunk_id: str,
    embedding: list[float] | tuple[float, ...],
) -> Chunk:
    normalized_embedding = normalize_embedding(embedding)
    if normalized_embedding is None:
        raise ValueError("embedding must not be None")

    chunk = db_session.get(Chunk, chunk_id)
    if chunk is None:
        raise ValueError(f"chunk not found: {chunk_id}")

    chunk.embedding = normalized_embedding
    db_session.add(chunk)
    db_session.flush()
    return chunk


def search_similar_chunks(
    db_session: Session,
    query_embedding: list[float] | tuple[float, ...],
    limit: int,
) -> list[ChunkSimilarityResult]:
    normalized_query = normalize_embedding(query_embedding)
    if normalized_query is None:
        raise ValueError("query_embedding must not be None")
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    if db_session.bind is not None and db_session.bind.dialect.name == "postgresql":
        return _search_similar_chunks_postgresql(db_session, normalized_query, limit)
    return _search_similar_chunks_sqlite(db_session, normalized_query, limit)


def _search_similar_chunks_postgresql(
    db_session: Session,
    query_embedding: list[float],
    limit: int,
) -> list[ChunkSimilarityResult]:
    distance_expression = Chunk.embedding.op("<=>", return_type=Float)(query_embedding)
    score_expression = (1.0 - distance_expression).label("score")
    statement = (
        select(Chunk, score_expression)
        .where(Chunk.embedding.is_not(None))
        .order_by(distance_expression)
        .limit(limit)
    )

    results: list[ChunkSimilarityResult] = []
    for chunk, score in db_session.execute(statement):
        results.append(
            ChunkSimilarityResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                source_type=chunk.source_type,
                asset_label=chunk.asset_label,
                preview_available=bool(chunk.asset_path),
                score=float(score),
            ),
        )
    return results


def _search_similar_chunks_sqlite(
    db_session: Session,
    query_embedding: list[float],
    limit: int,
) -> list[ChunkSimilarityResult]:
    statement = select(Chunk).where(Chunk.embedding.is_not(None))
    scored_chunks: list[ChunkSimilarityResult] = []

    for chunk in db_session.scalars(statement):
        if chunk.embedding is None:
            continue
        scored_chunks.append(
            ChunkSimilarityResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=chunk.page_number,
                source_type=chunk.source_type,
                asset_label=chunk.asset_label,
                preview_available=bool(chunk.asset_path),
                score=_cosine_similarity(query_embedding, chunk.embedding),
            ),
        )

    scored_chunks.sort(key=lambda item: item.score, reverse=True)
    return scored_chunks[:limit]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding dimensions must match")

    numerator = sum(left_item * right_item for left_item, right_item in zip(left, right, strict=True))
    left_norm = sqrt(sum(item * item for item in left))
    right_norm = sqrt(sum(item * item for item in right))

    if left_norm == 0 or right_norm == 0:
        raise ValueError("embedding norm must be greater than zero")

    return numerator / (left_norm * right_norm)
