from __future__ import annotations

import pytest

from backend.app.exceptions import AppError
from backend.infrastructure.llm.reranker_client import DashScopeRerankerClient


class FakeResponse:
    def __init__(self, *, status_code: int, output: dict | None = None, message: str = '') -> None:
        self.status_code = status_code
        self.output = output or {}
        self.message = message


def test_rerank_calls_dashscope_sdk_and_returns_indexes_in_response_order(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_call(**kwargs):
        captured_kwargs.update(kwargs)
        return FakeResponse(status_code=200, output={'results': [{'index': 2}, {'index': 0}]})

    monkeypatch.setattr('backend.infrastructure.llm.reranker_client.TextReRank.call', fake_call)

    client = DashScopeRerankerClient(api_key='test-key', model='gte-rerank-v2')

    result = client.rerank(query='q', documents=['a', 'b', 'c'], top_n=2)

    assert result == [2, 0]
    assert captured_kwargs == {
        'model': 'gte-rerank-v2',
        'query': 'q',
        'documents': ['a', 'b', 'c'],
        'top_n': 2,
        'return_documents': False,
        'api_key': 'test-key',
    }


def test_rerank_falls_back_to_prefix_when_results_are_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'backend.infrastructure.llm.reranker_client.TextReRank.call',
        lambda **kwargs: FakeResponse(status_code=200, output={'results': []}),
    )

    client = DashScopeRerankerClient(api_key='test-key', model='gte-rerank-v2')

    result = client.rerank(query='q', documents=['a', 'b', 'c'], top_n=2)

    assert result == [0, 1]


def test_rerank_raises_with_provider_message_when_provider_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        'backend.infrastructure.llm.reranker_client.TextReRank.call',
        lambda **kwargs: FakeResponse(status_code=400, message='Model not exist.'),
    )

    client = DashScopeRerankerClient(api_key='test-key', model='gte-rerank-v2')

    with pytest.raises(AppError) as exc_info:
        client.rerank(query='q', documents=['a'], top_n=1)

    assert exc_info.value.code == 'rerank_failed'
    assert 'Model not exist.' in exc_info.value.message
