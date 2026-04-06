from __future__ import annotations

from backend.app.exceptions import AppError
from backend.app.settings import BackendSettings
from backend.infrastructure.search.provider import AcceptanceSearchProvider, BraveSearchProvider


def create_search_provider(settings: BackendSettings) -> object:
    if settings.llm_mode == "acceptance" or settings.search_provider == "acceptance":
        return AcceptanceSearchProvider()

    if settings.search_provider == "brave":
        if not settings.search_api_key:
            raise AppError("缺少搜索服务 API Key", code="TOOL_UNAVAILABLE", status_code=500)
        return BraveSearchProvider(
            api_key=settings.search_api_key,
            timeout_seconds=settings.search_timeout_seconds,
            base_url=settings.search_base_url,
        )

    raise AppError("不支持的搜索 Provider", code="TOOL_UNAVAILABLE", status_code=500)
