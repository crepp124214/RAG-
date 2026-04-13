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
    def __init__(self, *, qa_service: KnowledgeBaseQAService, chat_client: Any | None = None) -> None:
        self.qa_service = qa_service
        self.chat_client = chat_client

    def create_session(self, db_session: Session, *, title: str = "新会话") -> ChatSession:
        session = SessionRepository(db_session).add(ChatSession(title=title))
        db_session.commit()
        db_session.refresh(session)
        log_event(logger, logging.INFO, "chat.session_created", session_id=session.id, title=session.title)
        return session

    def list_sessions(self, db_session: Session) -> list[ChatSession]:
        return SessionRepository(db_session).list_recent()

    def search_sessions(self, db_session: Session, *, keyword: str) -> list[ChatSession]:
        if not keyword.strip():
            return self.list_sessions(db_session)
        return SessionRepository(db_session).search(keyword.strip())

    def update_session(self, db_session: Session, *, session_id: str, title: str | None = None) -> ChatSession:
        session_repository = SessionRepository(db_session)
        session = session_repository.get_by_id(session_id)
        if session is None:
            raise AppError("会话不存在", code="session_not_found", status_code=404)

        if title is not None:
            session.title = title

        session_repository.update(session)
        db_session.commit()
        db_session.refresh(session)
        log_event(logger, logging.INFO, "chat.session_updated", session_id=session.id, title=session.title)
        return session

    def generate_session_title(self, db_session: Session, *, session_id: str) -> str:
        session = SessionRepository(db_session).get_by_id(session_id)
        if session is None:
            raise AppError("会话不存在", code="session_not_found", status_code=404)

        messages = MessageRepository(db_session).list_by_session_id(session_id)
        if not messages:
            raise AppError("会话无消息，无法生成标题", code="session_empty", status_code=400)

        first_user_message = next((msg for msg in messages if msg.role == "user"), None)
        if not first_user_message:
            raise AppError("会话无用户消息，无法生成标题", code="no_user_message", status_code=400)

        if self.chat_client is None:
            title = _generate_session_title(first_user_message.content)
        else:
            try:
                system_prompt = "你是一个会话标题生成助手。根据用户的第一条消息，生成一个简洁的会话标题（不超过50字符）。只返回标题文本，不要有其他内容。"
                user_prompt = f"用户消息：{first_user_message.content}\n\n请生成会话标题："
                title = self.chat_client.generate(system_prompt=system_prompt, user_prompt=user_prompt)
                title = title.strip().strip('"').strip("'")[:50]
            except Exception as exc:
                logger.warning("chat.auto_title_failed session_id=%s error=%s", session_id, str(exc))
                title = _generate_session_title(first_user_message.content)

        session.title = title
        SessionRepository(db_session).update(session)
        db_session.commit()
        db_session.refresh(session)
        log_event(logger, logging.INFO, "chat.title_generated", session_id=session.id, title=title)
        return title

    def export_session_markdown(self, db_session: Session, *, session_id: str) -> tuple[str, str]:
        session = SessionRepository(db_session).get_by_id(session_id)
        if session is None:
            raise AppError("会话不存在", code="session_not_found", status_code=404)

        messages = MessageRepository(db_session).list_by_session_id(session_id)

        lines = [
            f"# {session.title}",
            "",
            f"**创建时间**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**更新时间**: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

        for message in messages:
            role_label = "用户" if message.role == "user" else "助手"
            lines.append(f"## {role_label} ({message.created_at.strftime('%Y-%m-%d %H:%M:%S')})")
            lines.append("")
            lines.append(message.content)
            lines.append("")

            if message.citations:
                lines.append("### 引用")
                lines.append("")
                for idx, citation in enumerate(message.citations, 1):
                    lines.append(f"{idx}. **{citation['document_name']}**")
                    if citation.get('page_number'):
                        lines.append(f"   - 页码: {citation['page_number']}")
                    lines.append(f"   - 内容: {citation['content'][:100]}...")
                    lines.append("")

            if message.tool_calls:
                lines.append("### 工具调用")
                lines.append("")
                for tool_call in message.tool_calls:
                    lines.append(f"- **{tool_call['tool_name']}**")
                    lines.append(f"  - 状态: {tool_call['status']}")
                    if tool_call.get('result_summary'):
                        lines.append(f"  - 结果: {tool_call['result_summary']}")
                    lines.append("")

            lines.append("---")
            lines.append("")

        log_event(logger, logging.INFO, "chat.session_exported", session_id=session.id, message_count=len(messages))
        return session.title, "\n".join(lines)

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
