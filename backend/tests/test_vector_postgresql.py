from __future__ import annotations

from backend.infrastructure.vector.store import _search_similar_chunks_postgresql


class StubSession:
    def __init__(self) -> None:
        self.statements = []

    def execute(self, statement):
        self.statements.append(statement)
        return []


def test_postgresql_vector_search_builds_distance_query_without_attribute_error() -> None:
    db_session = StubSession()

    results = _search_similar_chunks_postgresql(db_session, [0.9, 0.1, 0.0], limit=3)

    assert results == []
    assert len(db_session.statements) == 1
    assert "<=>" in str(db_session.statements[0])
