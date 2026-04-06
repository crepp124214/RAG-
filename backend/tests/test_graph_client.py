from __future__ import annotations

import pytest

from backend.app.exceptions import AppError
from backend.infrastructure.llm.graph_client import QwenGraphExtractorClient


class FakeDashScopeResponse:
    def __init__(self, *, status_code: int, message: str = "", content: str = "[]") -> None:
        self.status_code = status_code
        self.message = message
        self.output = {"choices": [{"message": {"content": content}}]}


def test_qwen_graph_extractor_raises_on_non_success_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_call(**kwargs: object) -> FakeDashScopeResponse:
        del kwargs
        return FakeDashScopeResponse(status_code=500, message="dashscope unavailable")

    monkeypatch.setattr("backend.infrastructure.llm.graph_client.Generation.call", fake_call)
    client = QwenGraphExtractorClient(api_key="test-key", model="qwen-plus")

    with pytest.raises(AppError) as exc_info:
        client.extract_triples(text="平台A依赖服务B。")

    assert exc_info.value.code == "graph_extraction_failed"


def test_qwen_graph_extractor_parses_fenced_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_call(**kwargs: object) -> FakeDashScopeResponse:
        del kwargs
        return FakeDashScopeResponse(
            status_code=200,
            content='```json\n[{"subject":"平台A","predicate":"依赖","object":"服务B","entity_type":"system"}]\n```',
        )

    monkeypatch.setattr("backend.infrastructure.llm.graph_client.Generation.call", fake_call)
    client = QwenGraphExtractorClient(api_key="test-key", model="qwen-plus")

    triples = client.extract_triples(text="平台A依赖服务B。")

    assert triples == [
        {"subject": "平台A", "predicate": "依赖", "object": "服务B", "entity_type": "system"}
    ]
