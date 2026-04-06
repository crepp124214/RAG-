from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Document
from backend.infrastructure.vector.store import ChunkSimilarityResult, search_similar_chunks


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    content: str
    page_number: int | None
    source_type: str
    asset_label: str | None
    preview_available: bool
    score: float


class RetrievalService:
    def __init__(
        self,
        *,
        embedding_client: object,
        reranker_client: object,
        vector_top_k: int = 12,
        rerank_top_n: int = 5,
    ) -> None:
        self.embedding_client = embedding_client
        self.reranker_client = reranker_client
        self.vector_top_k = vector_top_k
        self.rerank_top_n = rerank_top_n

    def retrieve(self, db_session: Session, *, query: str) -> list[RetrievedChunk]:
        query_embedding = self.embedding_client.embed_texts([query])[0]
        candidates = search_similar_chunks(db_session, query_embedding, self.vector_top_k)
        if not candidates:
            return []

        document_names = self._load_document_names(db_session, candidates)
        reranked_indexes = self.reranker_client.rerank(
            query=query,
            documents=[candidate.content for candidate in candidates],
            top_n=min(self.rerank_top_n, len(candidates)),
        )

        selected_candidates = self._select_candidates(candidates, reranked_indexes)
        return [
            RetrievedChunk(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                document_name=document_names.get(item.document_id, item.document_id),
                chunk_index=item.chunk_index,
                content=item.content,
                page_number=item.page_number,
                source_type=item.source_type,
                asset_label=item.asset_label,
                preview_available=item.preview_available,
                score=item.score,
            )
            for item in selected_candidates
        ]

    def _load_document_names(
        self,
        db_session: Session,
        candidates: list[ChunkSimilarityResult],
    ) -> dict[str, str]:
        document_ids = sorted({candidate.document_id for candidate in candidates})
        statement = select(Document.id, Document.name).where(Document.id.in_(document_ids))
        return {document_id: document_name for document_id, document_name in db_session.execute(statement)}

    def _select_candidates(
        self,
        candidates: list[ChunkSimilarityResult],
        reranked_indexes: list[int],
    ) -> list[ChunkSimilarityResult]:
        if not reranked_indexes:
            return candidates[: self.rerank_top_n]
        return [candidates[index] for index in reranked_indexes if 0 <= index < len(candidates)]
