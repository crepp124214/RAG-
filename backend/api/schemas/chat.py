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
    citations: list[CitationData]
    tool_calls: list[ToolCallData]
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
    source_type: str = "text"
    asset_label: str | None = None
    preview_available: bool = False
    relation_label: str | None = None
    entity_path: str | None = None


class ToolCallData(BaseModel):
    tool_name: str
    arguments: dict
    status: str
    result_summary: str | None = None
    error_code: str | None = None
    error_detail: str | None = None


class ToolCallEventData(BaseModel):
    tool_name: str
    arguments: dict


class ChatQueryData(BaseModel):
    answer: str
    citations: list[CitationData]
    tool_calls: list[ToolCallData]
    user_message_id: str
    assistant_message_id: str


class ChatStreamStartData(BaseModel):
    session_id: str


class ChatStreamTokenData(BaseModel):
    content: str


class ChatStreamEndData(BaseModel):
    answer: str
    citations: list[CitationData]
    tool_calls: list[ToolCallData]
    user_message_id: str
    assistant_message_id: str
    session_id: str


class ChatStreamErrorData(BaseModel):
    code: str
    detail: str
