from __future__ import annotations

from pydantic import BaseModel


class CreateTagRequest(BaseModel):
    name: str
    color: str = "#409EFF"


class UpdateTagRequest(BaseModel):
    name: str | None = None
    color: str | None = None


class TagData(BaseModel):
    id: int
    name: str
    color: str
    created_at: str
    updated_at: str


class AddDocumentTagRequest(BaseModel):
    tag_id: int


class SetDocumentTagsRequest(BaseModel):
    tag_ids: list[int]


class DocumentPreviewChunk(BaseModel):
    chunk_index: int
    content: str
    source_type: str
    page_number: int | None


class BatchDeleteDocumentsRequest(BaseModel):
    document_ids: list[str]


class BatchTagDocumentsRequest(BaseModel):
    document_ids: list[str]
    tag_ids: list[int]
