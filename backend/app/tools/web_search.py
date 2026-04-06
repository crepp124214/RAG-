from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.tools.base import ToolCallRecord, ToolDefinition, ToolExecutionResult


class WebSearchTool:
    def __init__(self, *, search_provider: object) -> None:
        self.search_provider = search_provider

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="web_search",
            description="查询最新公开信息，返回标题、链接和摘要。",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
            handler=self.execute,
        )

    def execute(self, db_session: Session | None, arguments: dict[str, Any]) -> ToolExecutionResult:
        del db_session
        query = str(arguments.get("query", "")).strip()
        if not query:
            raise AppError("web_search 缺少 query", code="TOOL_BAD_ARGUMENTS", status_code=400)

        top_k = int(arguments.get("top_k", 5) or 5)
        if top_k <= 0:
            raise AppError("web_search 的 top_k 必须大于 0", code="TOOL_BAD_ARGUMENTS", status_code=400)

        results = self.search_provider.search(query=query, top_k=top_k)
        return ToolExecutionResult(
            output={"results": results},
            record=ToolCallRecord(
                tool_name="web_search",
                arguments={"query": query, "top_k": top_k},
                status="success",
                result_summary=f"命中 {len(results)} 条搜索结果",
            ),
            provider=type(self.search_provider).__name__,
        )
