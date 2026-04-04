from __future__ import annotations

from dashscope import TextEmbedding

from backend.app.exceptions import AppError


class DashScopeEmbeddingClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = TextEmbedding.call(
            model=self.model,
            input=texts,
            api_key=self.api_key,
        )

        status_code = getattr(response, "status_code", 500)
        if status_code != 200:
            message = getattr(response, "message", "embedding request failed")
            raise AppError(f"向量化失败: {message}", code="embedding_failed", status_code=502)

        output = getattr(response, "output", {}) or {}
        embeddings = output.get("embeddings", [])
        vectors = [item["embedding"] for item in embeddings if "embedding" in item]

        if len(vectors) != len(texts):
            raise AppError("向量化结果数量不匹配", code="embedding_result_mismatch", status_code=502)

        return vectors
