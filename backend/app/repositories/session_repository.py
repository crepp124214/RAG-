from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.models import Session as ChatSession


class SessionRepository:
    def __init__(self, db_session: Session) -> None:
        self.db_session = db_session

    def get_by_id(self, session_id: str) -> ChatSession | None:
        return self.db_session.get(ChatSession, session_id)

    def list_recent(self) -> list[ChatSession]:
        statement = select(ChatSession).order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        return list(self.db_session.scalars(statement))

    def add(self, session: ChatSession) -> ChatSession:
        self.db_session.add(session)
        self.db_session.flush()
        return session

    def update(self, session: ChatSession) -> ChatSession:
        self.db_session.add(session)
        self.db_session.flush()
        return session

    def search(self, keyword: str) -> list[ChatSession]:
        statement = (
            select(ChatSession)
            .where(ChatSession.title.ilike(f"%{keyword}%"))
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        )
        return list(self.db_session.scalars(statement))
