from __future__ import annotations

import requests

from backend.app.exceptions import AppError


class AcceptanceSearchProvider:
    def search(self, *, query: str, top_k: int) -> list[dict[str, str]]:
        return [
            {
                "title": f"验收搜索结果 {index + 1}",
                "url": f"https://acceptance.local/search/{index + 1}",
                "snippet": f"这是关于“{query}”的验收模式搜索结果。",
            }
            for index in range(top_k)
        ]


class BraveSearchProvider:
    def __init__(self, *, api_key: str, timeout_seconds: float, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url or "https://api.search.brave.com/res/v1/web/search"

    def search(self, *, query: str, top_k: int) -> list[dict[str, str]]:
        try:
            response = requests.get(
                self.base_url,
                params={"q": query, "count": top_k},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key,
                },
                timeout=self.timeout_seconds,
            )
        except (requests.Timeout, TimeoutError) as exc:
            raise AppError("搜索工具请求超时", code="TOOL_TIMEOUT", status_code=504) from exc
        except requests.RequestException as exc:
            raise AppError("搜索工具暂不可用", code="TOOL_UNAVAILABLE", status_code=502) from exc

        if response.status_code >= 500:
            raise AppError("搜索工具暂不可用", code="TOOL_UNAVAILABLE", status_code=502)
        if response.status_code >= 400:
            raise AppError("搜索工具执行失败", code="TOOL_EXECUTION_ERROR", status_code=502)

        payload = response.json() if response.content else {}
        web_payload = payload.get("web", {}) if isinstance(payload, dict) else {}
        results = web_payload.get("results", []) if isinstance(web_payload, dict) else []
        normalized: list[dict[str, str]] = []
        for item in results[:top_k]:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "url": str(item.get("url", "")).strip(),
                    "snippet": str(item.get("description", "")).strip(),
                }
            )
        return normalized
