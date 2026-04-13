from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class Tag(TimestampMixin, Base):
    __tablename__ = "document_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="#409EFF")

    document_relations = relationship(
        "DocumentTagRelation",
        back_populates="tag",
        cascade="all, delete-orphan",
    )


class DocumentTagRelation(TimestampMixin, Base):
    __tablename__ = "document_tag_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("document_tags.id", ondelete="CASCADE"),
        nullable=False,
    )

    tag = relationship("Tag", back_populates="document_relations")

    __table_args__ = (
        UniqueConstraint("document_id", "tag_id", name="uq_document_tag"),
    )
