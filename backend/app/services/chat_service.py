from __future__ import annotations

import logging
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.models import Message, Session as ChatSession
from backend.app.repositories.message_repository import MessageRepository
from backend.app.repositories.session_repository import SessionRepository
from backend.app.services.qa_service import KnowledgeBaseQAService, QAResult
from backend.infrastructure.observability import log_event


logger = logging.getLogger(__name__)


def _generate_session_title(query: str, *, max_length: int = 40) -> str:
    normalized = " ".join(query.split()).strip()
    if not normalized:
        return "新会话"
    return normalized if len(normalized) <= max_length else f"{normalized[:max_length].rstrip()}..."


def _serialize_citations(citations: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "document_id": citation.document_id,
            "document_name": citation.document_name,
            "chunk_id": citation.chunk_id,
            "content": citation.content,
            "page_number": citation.page_number,
            "source_type": citation.source_type,
            "asset_label": citation.asset_label,
            "preview_available": citation.preview_available,
            "relation_label": citation.relation_label,
            "entity_path": citation.entity_path,
        }
        for citation in citations
    ]


@dataclass(frozen=True)
class ChatStreamEvent:
    event: str
    data: dict[str, Any]


class ChatService:
    def __init__(self, *, qa_service: KnowledgeBaseQAService) -> None:
        self.qa_service = qa_service

    def create_session(self, db_session: Session, *, title: str = "新会话") -> ChatSession:
        session = SessionRepository(db_session).add(ChatSession(title=title))
        db_session.commit()
        db_session.refresh(session)
        log_event(logger, logging.INFO, "chat.session_created", session_id=session.id, title=session.title)
        return session

    def list_sessions(self, db_session: Session) -> list[ChatSession]:
        return SessionRepository(db_session).list_recent()

    def list_messages(self, db_session: Session, *, session_id: str) -> list[Message]:
        session = SessionRepository(db_session).get_by_id(session_id)
        if session is None:
            raise AppError("会话不存在", code="session_not_found", status_code=404)
        return MessageRepository(db_session).list_by_session_id(session_id)

    def query(self, db_session: Session, *, session_id: str, query: str) -> tuple[QAResult, Message, Message]:
        session_repository = SessionRepository(db_session)
        message_repository = MessageRepository(db_session)

        session = session_repository.get_by_id(session_id)
        if session is None:
            raise AppError("会话不存在", code="session_not_found", status_code=404)

        existing_messages = message_repository.list_by_session_id(session_id)
        if not existing_messages:
            session.title = _generate_session_title(query)
            db_session.add(session)
            db_session.flush()

        try:
            user_message = message_repository.add(
                Message(session_id=session_id, role="user", content=query, citations=[], tool_calls=[]),
            )
            qa_result = self.qa_service.ask(db_session, query=query)
            tool_calls = getattr(qa_result, "tool_calls", [])
            assistant_message = message_repository.add(
                Message(
                    session_id=session_id,
                    role="assistant",
                    content=qa_result.answer,
                    citations=_serialize_citations(qa_result.citations),
                    tool_calls=tool_calls,
                ),
            )

            db_session.commit()
            db_session.refresh(session)
            db_session.refresh(user_message)
            db_session.refresh(assistant_message)

            log_event(
                logger,
                logging.INFO,
                "chat.query_completed",
                session_id=session_id,
                user_message_id=user_message.id,
                assistant_message_id=assistant_message.id,
                citation_count=len(qa_result.citations),
                tool_count=len(tool_calls),
            )
            return qa_result, user_message, assistant_message
        except Exception:
            db_session.rollback()
            raise

    def stream_query(
        self,
        db_session: Session,
        *,
        session_id: str,
        query: str,
    ) -> Generator[ChatStreamEvent, None, None]:
        session_repository = SessionRepository(db_session)
        message_repository = MessageRepository(db_session)

        session = session_repository.get_by_id(session_id)
        if session is None:
            yield ChatStreamEvent(
                event="error",
                data={"code": "session_not_found", "detail": "会话不存在"},
            )
            return

        existing_messages = message_repository.list_by_session_id(session_id)
        if not existing_messages:
            session.title = _generate_session_title(query)
            db_session.add(session)

        try:
            citations, tool_calls, answer_stream = self.qa_service.stream_ask(db_session, query=query)

            yield ChatStreamEvent(event="message_start", data={"session_id": session_id})

            for citation in citations:
                yield ChatStreamEvent(
                    event="citation",
                    data={
                        "document_id": citation.document_id,
                        "document_name": citation.document_name,
                        "chunk_id": citation.chunk_id,
                        "content": citation.content,
                        "page_number": citation.page_number,
                        "source_type": citation.source_type,
                        "asset_label": citation.asset_label,
                        "preview_available": citation.preview_available,
                        "relation_label": citation.relation_label,
                        "entity_path": citation.entity_path,
                    },
                )

            for tool_call in tool_calls:
                yield ChatStreamEvent(
                    event="tool_call",
                    data={
                        "tool_name": tool_call["tool_name"],
                        "arguments": tool_call["arguments"],
                    },
                )
                yield ChatStreamEvent(event="tool_result", data=tool_call)

            answer_parts: list[str] = []
            for token in answer_stream:
                if not token:
                    continue
                answer_parts.append(token)
                yield ChatStreamEvent(event="token", data={"content": token})

            answer = "".join(answer_parts).strip()
            if not answer:
                raise AppError("问答生成结果为空", code="chat_generation_empty", status_code=502)

            user_message = message_repository.add(
                Message(session_id=session_id, role="user", content=query, citations=[], tool_calls=[]),
            )
            assistant_message = message_repository.add(
                Message(
                    session_id=session_id,
                    role="assistant",
                    content=answer,
                    citations=_serialize_citations(citations),
                    tool_calls=tool_calls,
                ),
            )

            db_session.commit()
            db_session.refresh(session)
            db_session.refresh(user_message)
            db_session.refresh(assistant_message)

            log_event(
                logger,
                logging.INFO,
                "chat.stream_completed",
                session_id=session_id,
                user_message_id=user_message.id,
                assistant_message_id=assistant_message.id,
                citation_count=len(citations),
                tool_count=len(tool_calls),
            )

            yield ChatStreamEvent(
                event="message_end",
                data={
                    "answer": answer,
                    "citations": _serialize_citations(citations),
                    "tool_calls": tool_calls,
                    "user_message_id": user_message.id,
                    "assistant_message_id": assistant_message.id,
                    "session_id": session_id,
                },
            )
        except Exception as exc:
            db_session.rollback()
            app_error = exc if isinstance(exc, AppError) else AppError(
                "流式问答失败",
                code="stream_query_failed",
                status_code=500,
            )
            log_event(
                logger,
                logging.ERROR,
                "chat.stream_failed",
                session_id=session_id,
                error_code=app_error.code,
                detail=app_error.message,
            )
            yield ChatStreamEvent(event="error", data={"code": app_error.code, "detail": app_error.message})
