from __future__ import annotations

from sqlalchemy import select

from backend.app.models import Chunk, Document
from backend.app.services.graph_service import GraphEvidence
from backend.app.services.retrieval_service import RetrievalService
from backend.infrastructure.database import create_database_engine, create_session_factory, initialize_database
from backend.infrastructure.vector.store import update_chunk_embedding
from backend.tests.support import create_workspace_temp_dir


class FakeEmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class FakeRerankerClient:
    def __init__(self, indexes: list[int]) -> None:
        self.indexes = indexes

    def rerank(self, *, query: str, documents: list[str], top_n: int) -> list[int]:
        return self.indexes[:top_n]


class FakeGraphStore:
    def __init__(self, evidence: list[GraphEvidence], *, error: Exception | None = None) -> None:
        self.evidence = evidence
        self.error = error
        self.queries: list[tuple[str, int]] = []

    def query_relations(self, *, query: str, limit: int) -> list[GraphEvidence]:
        self.queries.append((query, limit))
        if self.error is not None:
            raise self.error
        return self.evidence[:limit]


def test_retrieve_returns_reranked_chunks_with_document_names() -> None:
    temp_dir = create_workspace_temp_dir("retrieval")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'retrieval.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name="demo.txt",
            file_type="txt",
            status="READY",
            storage_path=str(temp_dir / "demo.txt"),
        )
        db_session.add(document)
        db_session.flush()

        first_chunk = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="first",
            source_type="text",
            page_number=1,
        )
        second_chunk = Chunk(
            document_id=document.id,
            chunk_index=1,
            content="second",
            source_type="text",
            page_number=2,
        )
        db_session.add_all([first_chunk, second_chunk])
        db_session.flush()
        update_chunk_embedding(db_session, first_chunk.id, [1.0, 0.0])
        update_chunk_embedding(db_session, second_chunk.id, [0.9, 0.1])
        db_session.commit()

    service = RetrievalService(
        embedding_client=FakeEmbeddingClient(),
        reranker_client=FakeRerankerClient([1, 0]),
        vector_top_k=12,
        rerank_top_n=2,
    )

    with session_factory() as db_session:
        results = service.retrieve(db_session, query="demo query")

    engine.dispose()

    assert len(results) == 2
    assert results[0].content == "second"
    assert results[0].document_name == "demo.txt"
    assert results[0].source_type == "text"
    assert results[0].asset_label is None
    assert results[0].preview_available is False
    assert results[1].content == "first"


def test_retrieve_returns_empty_list_when_no_chunks_exist() -> None:
    temp_dir = create_workspace_temp_dir("retrieval")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'empty.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    service = RetrievalService(
        embedding_client=FakeEmbeddingClient(),
        reranker_client=FakeRerankerClient([]),
        vector_top_k=12,
        rerank_top_n=5,
    )

    with session_factory() as db_session:
        results = service.retrieve(db_session, query="demo query")

    engine.dispose()

    assert results == []


def test_retrieve_ignores_chunks_with_mismatched_embedding_dimensions() -> None:
    temp_dir = create_workspace_temp_dir("retrieval-mismatch")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'mismatch.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name="mixed.txt",
            file_type="txt",
            status="READY",
            storage_path=str(temp_dir / "mixed.txt"),
        )
        db_session.add(document)
        db_session.flush()

        matched_chunk = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="matched",
            source_type="text",
            page_number=1,
        )
        mismatched_chunk = Chunk(
            document_id=document.id,
            chunk_index=1,
            content="mismatched",
            source_type="text",
            page_number=2,
        )
        db_session.add_all([matched_chunk, mismatched_chunk])
        db_session.flush()
        update_chunk_embedding(db_session, matched_chunk.id, [1.0, 0.0])
        update_chunk_embedding(db_session, mismatched_chunk.id, [1.0, 0.0, 0.0])
        db_session.commit()

    service = RetrievalService(
        embedding_client=FakeEmbeddingClient(),
        reranker_client=FakeRerankerClient([0]),
        vector_top_k=12,
        rerank_top_n=1,
    )

    with session_factory() as db_session:
        results = service.retrieve(db_session, query="demo query")

    engine.dispose()

    assert len(results) == 1
    assert results[0].content == "matched"


def test_retrieve_preserves_visual_chunk_metadata() -> None:
    temp_dir = create_workspace_temp_dir("retrieval-visual")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'visual.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name="report.pdf",
            file_type="pdf",
            status="READY",
            storage_path=str(temp_dir / "report.pdf"),
        )
        db_session.add(document)
        db_session.flush()

        visual_chunk = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="第 3 页柱状图显示第二季度销量最高。",
            source_type="image",
            page_number=3,
            asset_index=0,
            asset_label="第 3 页图片 1",
            asset_path=str(temp_dir / "report_assets" / "page-003-image-01.png"),
        )
        db_session.add(visual_chunk)
        db_session.flush()
        update_chunk_embedding(db_session, visual_chunk.id, [1.0, 0.0])
        db_session.commit()

    service = RetrievalService(
        embedding_client=FakeEmbeddingClient(),
        reranker_client=FakeRerankerClient([0]),
        vector_top_k=12,
        rerank_top_n=1,
    )

    with session_factory() as db_session:
        results = service.retrieve(db_session, query="图表表达了什么")

    engine.dispose()

    assert len(results) == 1
    assert results[0].source_type == "image"
    assert results[0].asset_label == "第 3 页图片 1"
    assert results[0].preview_available is True


def test_retrieve_merges_graph_evidence_for_relationship_queries() -> None:
    temp_dir = create_workspace_temp_dir("retrieval-graph")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'graph.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name="architecture.txt",
            file_type="txt",
            status="READY",
            storage_path=str(temp_dir / "architecture.txt"),
        )
        db_session.add(document)
        db_session.flush()

        chunk = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="A 服务依赖 B 服务。",
            source_type="text",
            page_number=1,
        )
        db_session.add(chunk)
        db_session.flush()
        update_chunk_embedding(db_session, chunk.id, [1.0, 0.0])
        db_session.commit()

        graph_store = FakeGraphStore(
            [
                GraphEvidence(
                    relation_id="rel-1",
                    document_id=document.id,
                    document_name="",
                    chunk_id=chunk.id,
                    content="A -> 依赖 -> B",
                    page_number=1,
                    relation_label="依赖",
                    entity_path="A -> B",
                    score=0.98,
                )
            ]
        )

    service = RetrievalService(
        embedding_client=FakeEmbeddingClient(),
        reranker_client=FakeRerankerClient([1, 0]),
        graph_store=graph_store,
        vector_top_k=12,
        rerank_top_n=2,
    )

    with session_factory() as db_session:
        results = service.retrieve(db_session, query="A 和 B 之间是什么关系？")

    engine.dispose()

    assert len(results) == 2
    assert graph_store.queries == [("A 和 B 之间是什么关系？", 2)]
    assert results[0].source_type == "graph"
    assert results[0].document_name == "architecture.txt"
    assert results[0].relation_label == "依赖"
    assert results[0].entity_path == "A -> B"
    assert results[1].source_type == "text"


def test_retrieve_falls_back_to_vector_when_graph_query_fails() -> None:
    temp_dir = create_workspace_temp_dir("retrieval-graph-fallback")
    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'graph-fallback.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name="architecture.txt",
            file_type="txt",
            status="READY",
            storage_path=str(temp_dir / "architecture.txt"),
        )
        db_session.add(document)
        db_session.flush()

        chunk = Chunk(
            document_id=document.id,
            chunk_index=0,
            content="A 服务依赖 B 服务。",
            source_type="text",
            page_number=1,
        )
        db_session.add(chunk)
        db_session.flush()
        update_chunk_embedding(db_session, chunk.id, [1.0, 0.0])
        db_session.commit()

    service = RetrievalService(
        embedding_client=FakeEmbeddingClient(),
        reranker_client=FakeRerankerClient([0]),
        graph_store=FakeGraphStore([], error=RuntimeError("neo4j down")),
        vector_top_k=12,
        rerank_top_n=1,
    )

    with session_factory() as db_session:
        results = service.retrieve(db_session, query="A 和 B 的关系是什么？")

    engine.dispose()

    assert len(results) == 1
    assert results[0].source_type == "text"
