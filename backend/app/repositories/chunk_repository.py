from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from backend.app.models import Chunk, Document


class ChunkRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def search_content(
        self,
        *,
        query: str,
        document_id: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        statement: Select = (
            select(Chunk, Document.name)
            .join(Document, Document.id == Chunk.document_id)
            .order_by(Chunk.chunk_index.asc())
        )
        if document_id:
            statement = statement.where(Chunk.document_id == document_id)

        rows = self.db_session.execute(statement).all()
        terms = [term for term in query.lower().split() if term]

        matches: list[tuple[int, Chunk, str]] = []
        for chunk, document_name in rows:
            content_lower = chunk.content.lower()
            score = sum(content_lower.count(term) for term in terms) if terms else 1
            if terms and score <= 0:
                continue
            matches.append((score, chunk, document_name))

        matches.sort(key=lambda item: (-item[0], item[1].chunk_index))
        return [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "document_name": document_name,
                "content": chunk.content,
                "page_number": chunk.page_number,
                "match_score": score,
            }
            for score, chunk, document_name in matches[:limit]
        ]
