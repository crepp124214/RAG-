from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.retrieval_service import RetrievedChunk
from backend.app.tools.base import ToolCallDecision, ToolCallRecord, ToolDefinition, ToolExecutionResult
from backend.app.tools.orchestrator import ToolOrchestrator
from backend.app.tools.registry import ToolRegistry


class FakeToolAwareChatClient:
    def __init__(self, *, decision: ToolCallDecision | None) -> None:
        self.decision = decision

    def decide_tool_call(self, *, query: str, tool_schemas: list[dict[str, object]]) -> ToolCallDecision | None:
        return self.decision


def _build_registry(result: ToolExecutionResult) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name=result.record.tool_name,
            description="demo",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            handler=lambda db_session, arguments: result,
        )
    )
    return registry


def test_orchestrator_returns_no_tool_calls_when_model_does_not_request_tool() -> None:
    orchestrator = ToolOrchestrator(
        registry=ToolRegistry(),
        chat_client=FakeToolAwareChatClient(decision=None),
    )

    outcome = orchestrator.run(db_session=None, query="普通知识库问题", allowed_tool_names=[])

    assert outcome.tool_calls == []
    assert outcome.tool_context is None


def test_orchestrator_executes_allowed_tool_and_returns_context() -> None:
    execution_result = ToolExecutionResult(
        output={"results": [{"title": "news", "url": "https://example.com", "snippet": "latest"}]},
        record=ToolCallRecord(
            tool_name="web_search",
            arguments={"query": "最新消息"},
            status="success",
            result_summary="命中 1 条搜索结果",
        ),
    )
    orchestrator = ToolOrchestrator(
        registry=_build_registry(execution_result),
        chat_client=FakeToolAwareChatClient(
            decision=ToolCallDecision(tool_name="web_search", arguments={"query": "最新消息"})
        ),
    )

    outcome = orchestrator.run(db_session=None, query="今天最新消息", allowed_tool_names=["web_search"])

    assert outcome.tool_calls[0].tool_name == "web_search"
    assert outcome.tool_calls[0].status == "success"
    assert "latest" in (outcome.tool_context or "")


def test_orchestrator_rejects_tool_request_outside_allowed_set() -> None:
    orchestrator = ToolOrchestrator(
        registry=ToolRegistry(),
        chat_client=FakeToolAwareChatClient(
            decision=ToolCallDecision(tool_name="web_search", arguments={"query": "最新消息"})
        ),
    )

    outcome = orchestrator.run(db_session=None, query="今天最新消息", allowed_tool_names=[])

    assert outcome.tool_calls[0].tool_name == "web_search"
    assert outcome.tool_calls[0].status == "failed"
    assert outcome.tool_calls[0].error_code == "TOOL_SECURITY_BLOCKED"
