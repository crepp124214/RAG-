from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Document


class DocumentRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_by_id(self, document_id: str) -> Document | None:
        return self.db_session.get(Document, document_id)

    def get_by_storage_path(self, storage_path: str) -> Document | None:
        statement = select(Document).where(Document.storage_path == storage_path)
        return self.db_session.scalar(statement)

    def add(self, document: Document) -> Document:
        self.db_session.add(document)
        self.db_session.flush()
        return document
