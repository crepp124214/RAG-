from __future__ import annotations

import pytest

from backend.app.exceptions import AppError
from backend.infrastructure.llm.embedding_client import DashScopeEmbeddingClient


class FakeResponse:
    def __init__(self, *, status_code: int, embeddings: list[list[float]] | None = None, message: str = "") -> None:
        self.status_code = status_code
        self.message = message
        self.output = {
            "embeddings": [{"embedding": embedding} for embedding in (embeddings or [])],
        }


def test_embed_texts_returns_vectors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.embedding_client.TextEmbedding.call",
        lambda **kwargs: FakeResponse(status_code=200, embeddings=[[0.1, 0.2], [0.3, 0.4]]),
    )

    client = DashScopeEmbeddingClient(api_key="test-key", model="text-embedding-v1")
    result = client.embed_texts(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]


def test_embed_texts_raises_when_provider_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.embedding_client.TextEmbedding.call",
        lambda **kwargs: FakeResponse(status_code=500, message="provider down"),
    )

    client = DashScopeEmbeddingClient(api_key="test-key", model="text-embedding-v1")

    with pytest.raises(AppError) as exc_info:
        client.embed_texts(["a"])

    assert exc_info.value.code == "embedding_failed"


def test_embed_texts_rejects_result_count_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.infrastructure.llm.embedding_client.TextEmbedding.call",
        lambda **kwargs: FakeResponse(status_code=200, embeddings=[[0.1, 0.2]]),
    )

    client = DashScopeEmbeddingClient(api_key="test-key", model="text-embedding-v1")

    with pytest.raises(AppError) as exc_info:
        client.embed_texts(["a", "b"])

    assert exc_info.value.code == "embedding_result_mismatch"
