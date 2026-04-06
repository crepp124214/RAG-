from __future__ import annotations

import pytest

from backend.app.exceptions import AppError
from backend.app.tools.web_search import WebSearchTool
from backend.infrastructure.search import AcceptanceSearchProvider, BraveSearchProvider


def test_acceptance_search_provider_returns_deterministic_results() -> None:
    provider = AcceptanceSearchProvider()
    tool = WebSearchTool(search_provider=provider)

    result = tool.execute(None, {"query": "今天的验收状态", "top_k": 2})

    assert result.record.status == "success"
    assert result.output["results"][0]["title"]
    assert result.output["results"][0]["url"]
    assert result.output["results"][0]["snippet"]


def test_brave_search_provider_maps_timeout_to_tool_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = BraveSearchProvider(api_key="test-key", timeout_seconds=1.0)

    def raise_timeout(*args, **kwargs):
        raise TimeoutError("timed out")

    monkeypatch.setattr("backend.infrastructure.search.provider.requests.get", raise_timeout)

    with pytest.raises(AppError) as exc_info:
        provider.search(query="latest news", top_k=3)

    assert exc_info.value.code == "TOOL_TIMEOUT"
