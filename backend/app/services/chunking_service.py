from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DEFAULT_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", " ", ""]


@dataclass(frozen=True)
class ChunkPayload:
    document_id: str
    chunk_index: int
    content: str
    source_type: str
    page_number: int | None
    metadata: dict[str, Any]


class DocumentChunkingService:
    def __init__(self, *, chunk_size: int = 800, chunk_overlap: int = 150) -> None:
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=DEFAULT_SEPARATORS,
        )

    def split_documents(
        self,
        documents: list[Document],
        *,
        document_id: str,
        source_type: str = "text",
    ) -> list[ChunkPayload]:
        split_documents = self.text_splitter.split_documents(documents)

        chunks: list[ChunkPayload] = []
        for index, document in enumerate(split_documents):
            content = document.page_content.strip()
            if not content:
                continue

            normalized_metadata = dict(document.metadata)
            page_number = normalized_metadata.get("page_number")
            if not isinstance(page_number, int):
                raw_page = normalized_metadata.get("page")
                page_number = raw_page + 1 if isinstance(raw_page, int) else None

            normalized_metadata["document_id"] = document_id
            normalized_metadata["chunk_index"] = index
            normalized_metadata["source_type"] = normalized_metadata.get("source_type", source_type)
            normalized_metadata["page_number"] = page_number

            chunks.append(
                ChunkPayload(
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    source_type=normalized_metadata["source_type"],
                    page_number=page_number,
                    metadata=normalized_metadata,
                )
            )

        return chunks
