from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.tag import DocumentTagRelation, Tag


class TagRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_by_id(self, tag_id: int) -> Tag | None:
        return self.db_session.get(Tag, tag_id)

    def get_by_name(self, name: str) -> Tag | None:
        statement = select(Tag).where(Tag.name == name)
        return self.db_session.scalar(statement)

    def list_all(self) -> list[Tag]:
        statement = select(Tag).order_by(Tag.created_at.desc())
        return list(self.db_session.scalars(statement).all())

    def add(self, tag: Tag) -> Tag:
        self.db_session.add(tag)
        self.db_session.flush()
        return tag

    def delete(self, tag: Tag) -> None:
        self.db_session.delete(tag)

    def get_document_tags(self, document_id: str) -> list[Tag]:
        statement = (
            select(Tag)
            .join(DocumentTagRelation)
            .where(DocumentTagRelation.document_id == document_id)
            .order_by(Tag.name.asc())
        )
        return list(self.db_session.scalars(statement).all())

    def add_document_tag(self, document_id: str, tag_id: int) -> DocumentTagRelation:
        relation = DocumentTagRelation(document_id=document_id, tag_id=tag_id)
        self.db_session.add(relation)
        self.db_session.flush()
        return relation

    def remove_document_tag(self, document_id: str, tag_id: int) -> None:
        statement = select(DocumentTagRelation).where(
            DocumentTagRelation.document_id == document_id,
            DocumentTagRelation.tag_id == tag_id,
        )
        relation = self.db_session.scalar(statement)
        if relation:
            self.db_session.delete(relation)

    def set_document_tags(self, document_id: str, tag_ids: list[int]) -> None:
        statement = select(DocumentTagRelation).where(DocumentTagRelation.document_id == document_id)
        existing_relations = list(self.db_session.scalars(statement).all())

        for relation in existing_relations:
            self.db_session.delete(relation)

        for tag_id in tag_ids:
            relation = DocumentTagRelation(document_id=document_id, tag_id=tag_id)
            self.db_session.add(relation)

        self.db_session.flush()

    def tag_exists(self, document_id: str, tag_id: int) -> bool:
        statement = select(DocumentTagRelation).where(
            DocumentTagRelation.document_id == document_id,
            DocumentTagRelation.tag_id == tag_id,
        )
        return self.db_session.scalar(statement) is not None
