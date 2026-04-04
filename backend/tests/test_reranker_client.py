from __future__ import annotations

import pytest

from backend.app.exceptions import AppError
from backend.infrastructure.llm.reranker_client import DashScopeRerankerClient


class FakeResponse:
    def __init__(self, *, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


def test_rerank_returns_indexes_in_response_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.reranker_client.requests.post",
        lambda *args, **kwargs: FakeResponse(status_code=200, payload={"results": [{"index": 2}, {"index": 0}]}),
    )

    client = DashScopeRerankerClient(api_key="test-key", model="bge-reranker")

    result = client.rerank(query="q", documents=["a", "b", "c"], top_n=2)

    assert result == [2, 0]


def test_rerank_falls_back_to_prefix_when_results_are_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.reranker_client.requests.post",
        lambda *args, **kwargs: FakeResponse(status_code=200, payload={"results": []}),
    )

    client = DashScopeRerankerClient(api_key="test-key", model="bge-reranker")

    result = client.rerank(query="q", documents=["a", "b", "c"], top_n=2)

    assert result == [0, 1]


def test_rerank_raises_when_provider_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.reranker_client.requests.post",
        lambda *args, **kwargs: FakeResponse(status_code=500),
    )

    client = DashScopeRerankerClient(api_key="test-key", model="bge-reranker")

    with pytest.raises(AppError) as exc_info:
        client.rerank(query="q", documents=["a"], top_n=1)

    assert exc_info.value.code == "rerank_failed"
