from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, generate_id
from backend.infrastructure.vector.types import EmbeddingVector


class Chunk(TimestampMixin, Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    asset_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    bbox: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector(), nullable=True)

    document = relationship("Document", back_populates="chunks")
