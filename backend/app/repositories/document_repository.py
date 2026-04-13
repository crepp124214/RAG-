from __future__ import annotations

from sqlalchemy import select, func, or_
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

    def list_documents(
        self,
        *,
        search: str | None = None,
        tag_ids: list[int] | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Document]:
        statement = select(Document)

        if search:
            statement = statement.where(Document.name.ilike(f"%{search}%"))

        if tag_ids:
            from backend.app.models.tag import DocumentTagRelation
            statement = statement.join(DocumentTagRelation).where(
                DocumentTagRelation.tag_id.in_(tag_ids)
            )

        sort_column = getattr(Document, sort_by, Document.created_at)
        if order == "asc":
            statement = statement.order_by(sort_column.asc())
        else:
            statement = statement.order_by(sort_column.desc())

        statement = statement.offset(offset)
        if limit:
            statement = statement.limit(limit)

        return list(self.db_session.scalars(statement).all())

    def count_documents(
        self,
        *,
        search: str | None = None,
        tag_ids: list[int] | None = None,
    ) -> int:
        statement = select(func.count(Document.id))

        if search:
            statement = statement.where(Document.name.ilike(f"%{search}%"))

        if tag_ids:
            from backend.app.models.tag import DocumentTagRelation
            statement = statement.join(DocumentTagRelation).where(
                DocumentTagRelation.tag_id.in_(tag_ids)
            )

        return int(self.db_session.scalar(statement) or 0)

    def get_by_ids(self, document_ids: list[str]) -> list[Document]:
        statement = select(Document).where(Document.id.in_(document_ids))
        return list(self.db_session.scalars(statement).all())

    def delete_many(self, document_ids: list[str]) -> None:
        documents = self.get_by_ids(document_ids)
        for document in documents:
            self.db_session.delete(document)
