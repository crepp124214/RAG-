from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Document
from backend.app.services.graph_service import GraphEvidence
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
    relation_label: str | None = None
    entity_path: str | None = None


class RetrievalService:
    def __init__(
        self,
        *,
        embedding_client: object,
        reranker_client: object,
        graph_store: object | None = None,
        vector_top_k: int = 12,
        rerank_top_n: int = 5,
    ) -> None:
        self.embedding_client = embedding_client
        self.reranker_client = reranker_client
        self.graph_store = graph_store
        self.vector_top_k = vector_top_k
        self.rerank_top_n = rerank_top_n

    def retrieve(self, db_session: Session, *, query: str) -> list[RetrievedChunk]:
        vector_candidates = self._query_vector_candidates(db_session, query)
        graph_candidates = self._query_graph_candidates(db_session, query)
        combined_candidates = [*vector_candidates, *graph_candidates]
        if not combined_candidates:
            return []

        reranked_indexes = self.reranker_client.rerank(
            query=query,
            documents=[candidate.content for candidate in combined_candidates],
            top_n=min(self.rerank_top_n, len(combined_candidates)),
        )
        return self._select_candidates(combined_candidates, reranked_indexes)

    def _query_vector_candidates(self, db_session: Session, query: str) -> list[RetrievedChunk]:
        query_embedding = self.embedding_client.embed_texts([query])[0]
        candidates = search_similar_chunks(db_session, query_embedding, self.vector_top_k)
        if not candidates:
            return []

        document_names = self._load_document_names(db_session, candidates)
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
            for item in candidates
        ]

    def _query_graph_candidates(self, db_session: Session, query: str) -> list[RetrievedChunk]:
        if self.graph_store is None or not self._need_graph_retrieval(query):
            return []
        try:
            graph_evidence = self.graph_store.query_relations(query=query, limit=self.rerank_top_n)
        except Exception:
            return []
        document_names = self._load_graph_document_names(db_session, graph_evidence)
        return [self._from_graph_evidence(item, document_names=document_names) for item in graph_evidence]

    def _load_document_names(
        self,
        db_session: Session,
        candidates: list[ChunkSimilarityResult],
    ) -> dict[str, str]:
        document_ids = sorted({candidate.document_id for candidate in candidates})
        statement = select(Document.id, Document.name).where(Document.id.in_(document_ids))
        return {document_id: document_name for document_id, document_name in db_session.execute(statement)}

    def _load_graph_document_names(
        self,
        db_session: Session,
        candidates: list[GraphEvidence],
    ) -> dict[str, str]:
        document_ids = sorted({candidate.document_id for candidate in candidates if not candidate.document_name})
        if not document_ids:
            return {}
        statement = select(Document.id, Document.name).where(Document.id.in_(document_ids))
        return {document_id: document_name for document_id, document_name in db_session.execute(statement)}

    def _select_candidates(
        self,
        candidates: list[RetrievedChunk],
        reranked_indexes: list[int],
    ) -> list[RetrievedChunk]:
        if not reranked_indexes:
            return candidates[: self.rerank_top_n]
        return [candidates[index] for index in reranked_indexes if 0 <= index < len(candidates)]

    def _need_graph_retrieval(self, query: str) -> bool:
        keywords = ["关系", "依赖", "关联", "影响", "链路", "谁", "总结", "之间", "上下游"]
        lowered = query.casefold()
        return any(keyword in query or keyword in lowered for keyword in keywords)

    def _from_graph_evidence(
        self,
        evidence: GraphEvidence,
        *,
        document_names: dict[str, str],
    ) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=evidence.chunk_id,
            document_id=evidence.document_id,
            document_name=evidence.document_name or document_names.get(evidence.document_id, evidence.document_id),
            chunk_index=-1,
            content=evidence.content,
            page_number=evidence.page_number,
            source_type="graph",
            asset_label=None,
            preview_available=False,
            score=evidence.score,
            relation_label=evidence.relation_label,
            entity_path=evidence.entity_path,
        )
