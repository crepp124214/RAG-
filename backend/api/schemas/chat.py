from __future__ import annotations

from pydantic import BaseModel, Field


class CreateSessionData(BaseModel):
    session_id: str
    title: str


class SessionListItemData(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageListItemData(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: str
    updated_at: str


class ChatQueryRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)


class CitationData(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    content: str
    page_number: int | None


class ChatQueryData(BaseModel):
    answer: str
    citations: list[CitationData]
    user_message_id: str
    assistant_message_id: str


class ChatStreamStartData(BaseModel):
    session_id: str


class ChatStreamTokenData(BaseModel):
    content: str


class ChatStreamEndData(BaseModel):
    answer: str
    citations: list[CitationData]
    user_message_id: str
    assistant_message_id: str
    session_id: str


class ChatStreamErrorData(BaseModel):
    code: str
    detail: str
