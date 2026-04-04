from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, generate_id


class Session(TimestampMixin, Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
