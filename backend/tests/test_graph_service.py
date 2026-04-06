from __future__ import annotations

from backend.app.services.graph_service import GraphEvidence, GraphTripleExtractionService


class FakeExtractorClient:
    def __init__(self, responses: list[list[dict[str, object]]]) -> None:
        self.responses = responses

    def extract_triples(self, *, text: str) -> list[dict[str, object]]:
        return self.responses.pop(0)


def test_graph_triple_extraction_normalizes_and_deduplicates_triples() -> None:
    service = GraphTripleExtractionService(
        extractor_client=FakeExtractorClient(
            [
                [
                    {"subject": " 平台A ", "predicate": "依赖", "object": " 服务B ", "entity_type": "system"},
                    {"subject": "平台A", "predicate": "依赖", "object": "服务B", "entity_type": "system"},
                    {"subject": "", "predicate": "关联", "object": "无效"},
                    {"subject": "x" * 260, "predicate": "关联", "object": "过长"},
                ]
            ]
        )
    )

    triples = service.extract_from_chunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        page_number=2,
        content="平台A依赖服务B。",
    )

    assert len(triples) == 1
    assert triples[0].subject == "平台A"
    assert triples[0].predicate == "依赖"
    assert triples[0].object == "服务B"
    assert triples[0].document_id == "doc-1"
    assert triples[0].source_chunk_id == "chunk-1"
    assert triples[0].page_number == 2


def test_graph_evidence_preserves_relation_fields() -> None:
    evidence = GraphEvidence(
        relation_id="rel-1",
        document_id="doc-1",
        document_name="design.txt",
        chunk_id="chunk-1",
        content="平台A依赖服务B。",
        page_number=3,
        relation_label="依赖",
        entity_path="平台A -> 依赖 -> 服务B",
        score=0.9,
    )

    assert evidence.relation_label == "依赖"
    assert evidence.entity_path == "平台A -> 依赖 -> 服务B"
