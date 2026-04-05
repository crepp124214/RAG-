from __future__ import annotations

from dashscope import TextReRank

from backend.app.exceptions import AppError


class DashScopeRerankerClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def rerank(self, *, query: str, documents: list[str], top_n: int) -> list[int]:
        if not documents:
            return []

        response = TextReRank.call(
            model=self.model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
            return_documents=False,
            api_key=self.api_key,
        )

        if getattr(response, 'status_code', 500) != 200:
            message = getattr(response, 'message', 'rerank request failed')
            raise AppError(f'????: {message}', code='rerank_failed', status_code=502)

        output = getattr(response, 'output', {}) or {}
        results = output.get('results', []) if isinstance(output, dict) else getattr(output, 'results', [])
        if not results:
            return list(range(min(top_n, len(documents))))

        return [item['index'] for item in results if 'index' in item][:top_n]
