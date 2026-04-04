from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Message


class MessageRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def list_by_session_id(self, session_id: str) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        return list(self.db_session.scalars(statement))

    def add(self, message: Message) -> Message:
        self.db_session.add(message)
        self.db_session.flush()
        return message
