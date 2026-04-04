from __future__ import annotations

import requests

from backend.app.exceptions import AppError


class DashScopeRerankerClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/rerank/models"

    def rerank(self, *, query: str, documents: list[str], top_n: int) -> list[int]:
        if not documents:
            return []

        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "query": {"text": query},
                "documents": [{"text": content} for content in documents],
                "top_n": min(top_n, len(documents)),
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise AppError("重排失败", code="rerank_failed", status_code=502)

        payload = response.json()
        results = payload.get("results") or payload.get("output", {}).get("results") or []
        if not results:
            return list(range(min(top_n, len(documents))))

        return [item["index"] for item in results if "index" in item][:top_n]
