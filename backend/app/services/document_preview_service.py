from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.models import Chunk
from backend.app.repositories.document_repository import DocumentRepository


logger = logging.getLogger(__name__)


def get_document_preview(db_session: Session, document_id: str, *, limit: int = 5) -> list[dict]:
    document_repository = DocumentRepository(db_session)

    document = document_repository.get_by_id(document_id)
    if not document:
        raise AppError("文档不存在", code="document_not_found", status_code=404)

    from sqlalchemy import select
    statement = (
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index.asc())
        .limit(limit)
    )
    chunks = list(db_session.scalars(statement).all())

    return [
        {
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "source_type": chunk.source_type,
            "page_number": chunk.page_number,
        }
        for chunk in chunks
    ]
