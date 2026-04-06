from __future__ import annotations

import json
import logging
from collections.abc import Generator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.api.deps.database import get_db_session
from backend.api.schemas.chat import (
    ChatQueryData,
    ChatQueryRequest,
    ChatStreamEndData,
    ChatStreamErrorData,
    ChatStreamStartData,
    ToolCallData,
    ToolCallEventData,
    ChatStreamTokenData,
    CitationData,
    CreateSessionData,
    MessageListItemData,
    SessionListItemData,
)
from backend.api.schemas.response import success_response
from backend.app.exceptions import AppError
from backend.app.services.chat_service import ChatService
from backend.app.services.qa_service import KnowledgeBaseQAService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.tools import DocumentLookupTool, ToolOrchestrator, ToolRegistry, WebSearchTool
from backend.infrastructure.llm import create_chat_client, create_embedding_client, create_reranker_client
from backend.infrastructure.search import create_search_provider


router = APIRouter(prefix='/chat', tags=['chat'])
logger = logging.getLogger(__name__)


def _format_sse_event(*, event: str, data: dict) -> str:
    return f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'


def get_chat_service(request: Request) -> ChatService:
    settings = request.app.state.settings
    chat_client = create_chat_client(settings)
    retrieval_service = RetrievalService(
        embedding_client=create_embedding_client(settings),
        reranker_client=create_reranker_client(settings),
        vector_top_k=settings.vector_top_k,
        rerank_top_n=settings.rerank_top_n,
    )
    tool_registry = ToolRegistry()
    tool_registry.register(DocumentLookupTool().definition())
    try:
        tool_registry.register(WebSearchTool(search_provider=create_search_provider(settings)).definition())
    except AppError as exc:
        logger.warning(
            "chat.web_search_disabled code=%s detail=%s",
            exc.code,
            exc.message,
        )
    qa_service = KnowledgeBaseQAService(
        retrieval_service=retrieval_service,
        chat_client=chat_client,
        tool_orchestrator=ToolOrchestrator(registry=tool_registry, chat_client=chat_client),
    )
    return ChatService(qa_service=qa_service)


@router.post('/sessions')
def create_session(
    db_session: Session = Depends(get_db_session),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict:
    session = chat_service.create_session(db_session)
    return success_response(
        message='会话创建成功',
        data=CreateSessionData(session_id=session.id, title=session.title).model_dump(),
    )


@router.get('/sessions')
def list_sessions(
    db_session: Session = Depends(get_db_session),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict:
    sessions = chat_service.list_sessions(db_session)
    return success_response(
        message='获取会话列表成功',
        data=[
            SessionListItemData(
                id=session.id,
                title=session.title,
                created_at=session.created_at.isoformat(),
                updated_at=session.updated_at.isoformat(),
            ).model_dump()
            for session in sessions
        ],
    )


@router.get('/sessions/{session_id}/messages')
def list_messages(
    session_id: str,
    db_session: Session = Depends(get_db_session),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict:
    messages = chat_service.list_messages(db_session, session_id=session_id)
    return success_response(
        message='获取消息列表成功',
        data=[
            MessageListItemData(
                id=message.id,
                session_id=message.session_id,
                role=message.role,
                content=message.content,
                citations=[CitationData(**item) for item in (message.citations or [])],
                tool_calls=[ToolCallData(**item) for item in (message.tool_calls or [])],
                created_at=message.created_at.isoformat(),
                updated_at=message.updated_at.isoformat(),
            ).model_dump()
            for message in messages
        ],
    )


@router.post('/query')
def query_chat(
    payload: ChatQueryRequest,
    db_session: Session = Depends(get_db_session),
    chat_service: ChatService = Depends(get_chat_service),
) -> dict:
    qa_result, user_message, assistant_message = chat_service.query(
        db_session,
        session_id=payload.session_id,
        query=payload.query,
    )
    return success_response(
        message='问答成功',
        data=ChatQueryData(
            answer=qa_result.answer,
            citations=[
                CitationData(
                    document_id=item.document_id,
                    document_name=item.document_name,
                    chunk_id=item.chunk_id,
                    content=item.content,
                    page_number=item.page_number,
                    source_type=item.source_type,
                    asset_label=item.asset_label,
                    preview_available=item.preview_available,
                )
                for item in qa_result.citations
            ],
            tool_calls=[ToolCallData(**item) for item in qa_result.tool_calls],
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
        ).model_dump(),
    )


@router.post('/stream')
def stream_chat(
    payload: ChatQueryRequest,
    request: Request,
    chat_service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    session_factory = request.app.state.db_session_factory

    def event_generator() -> Generator[str, None, None]:
        citations: list[CitationData] = []

        with session_factory() as db_session:
            for item in chat_service.stream_query(
                db_session,
                session_id=payload.session_id,
                query=payload.query,
            ):
                if item.event == 'message_start':
                    yield _format_sse_event(
                        event=item.event,
                        data=ChatStreamStartData(**item.data).model_dump(),
                    )
                    continue

                if item.event == 'citation':
                    citation = CitationData(**item.data)
                    citations.append(citation)
                    yield _format_sse_event(event=item.event, data=citation.model_dump())
                    continue

                if item.event == 'token':
                    yield _format_sse_event(
                        event=item.event,
                        data=ChatStreamTokenData(**item.data).model_dump(),
                    )
                    continue

                if item.event == 'tool_call':
                    yield _format_sse_event(
                        event=item.event,
                        data=ToolCallEventData(**item.data).model_dump(),
                    )
                    continue

                if item.event == 'tool_result':
                    yield _format_sse_event(
                        event=item.event,
                        data=ToolCallData(**item.data).model_dump(),
                    )
                    continue

                if item.event == 'message_end':
                    end_payload = ChatStreamEndData(
                        citations=citations,
                        tool_calls=[ToolCallData(**tool_call) for tool_call in item.data.get("tool_calls", [])],
                        answer=item.data["answer"],
                        user_message_id=item.data["user_message_id"],
                        assistant_message_id=item.data["assistant_message_id"],
                        session_id=item.data["session_id"],
                    )
                    yield _format_sse_event(event=item.event, data=end_payload.model_dump())
                    continue

                if item.event == 'error':
                    yield _format_sse_event(
                        event=item.event,
                        data=ChatStreamErrorData(**item.data).model_dump(),
                    )

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )
