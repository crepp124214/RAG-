from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session


ToolHandler = Callable[[Session | None, dict[str, Any]], "ToolExecutionResult"]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def to_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


@dataclass(frozen=True)
class ToolCallDecision:
    tool_name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolCallRecord:
    tool_name: str
    arguments: dict[str, Any]
    status: str
    result_summary: str | None = None
    error_code: str | None = None
    error_detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "status": self.status,
            "result_summary": self.result_summary,
            "error_code": self.error_code,
            "error_detail": self.error_detail,
        }


@dataclass(frozen=True)
class ToolExecutionResult:
    output: dict[str, Any]
    record: ToolCallRecord
    provider: str | None = None


@dataclass(frozen=True)
class ToolOrchestrationOutcome:
    tool_calls: list[ToolCallRecord]
    tool_context: str | None
