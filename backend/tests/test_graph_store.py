from __future__ import annotations

from backend.infrastructure.graph.store import _build_query_terms


def test_build_query_terms_extracts_entity_terms_from_relationship_question() -> None:
    terms = _build_query_terms("系统 A 和 系统 B 之间是什么关系？")

    assert "系统" in terms
    assert "系统 a 和 系统 b 之间是什么关系？" not in terms


def test_build_query_terms_splits_compact_chinese_relationship_question() -> None:
    terms = _build_query_terms("系统A和系统B之间是什么关系？")

    assert "系统a" in terms
    assert "系统b" in terms
    assert "系统a和系统b之间是什么关系" not in terms
