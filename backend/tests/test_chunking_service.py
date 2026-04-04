from __future__ import annotations

from langchain_core.documents import Document

from backend.app.services.chunking_service import DocumentChunkingService


def test_split_documents_returns_stable_chunks_for_same_input() -> None:
    service = DocumentChunkingService(chunk_size=12, chunk_overlap=2)
    documents = [Document(page_content="第一段。第二段。第三段。", metadata={"page_number": 1})]

    first = service.split_documents(documents, document_id="doc-1")
    second = service.split_documents(documents, document_id="doc-1")

    assert [chunk.content for chunk in first] == [chunk.content for chunk in second]
    assert [chunk.chunk_index for chunk in first] == [chunk.chunk_index for chunk in second]


def test_split_documents_keeps_required_metadata_fields() -> None:
    service = DocumentChunkingService(chunk_size=12, chunk_overlap=2)
    documents = [
        Document(
            page_content="这是一个需要切分的段落。这是第二句。",
            metadata={"page_number": 3, "source": "demo.txt"},
        )
    ]

    chunks = service.split_documents(documents, document_id="doc-2")

    assert len(chunks) >= 1
    first = chunks[0]
    assert first.document_id == "doc-2"
    assert first.chunk_index == 0
    assert first.source_type == "text"
    assert first.page_number == 3
    assert first.metadata["document_id"] == "doc-2"
    assert first.metadata["chunk_index"] == 0
    assert first.metadata["source_type"] == "text"
    assert first.metadata["page_number"] == 3


def test_split_documents_generates_chunk_for_short_document() -> None:
    service = DocumentChunkingService(chunk_size=100, chunk_overlap=10)
    documents = [Document(page_content="短文档内容", metadata={"page_number": 1})]

    chunks = service.split_documents(documents, document_id="doc-3")

    assert len(chunks) == 1
    assert chunks[0].content == "短文档内容"


def test_split_documents_skips_empty_content() -> None:
    service = DocumentChunkingService(chunk_size=20, chunk_overlap=5)
    documents = [Document(page_content="   ", metadata={"page_number": 1})]

    chunks = service.split_documents(documents, document_id="doc-4")

    assert chunks == []
