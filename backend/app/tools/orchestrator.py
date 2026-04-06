from __future__ import annotations

import json
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.tools.base import ToolCallRecord, ToolOrchestrationOutcome
from backend.app.tools.registry import ToolRegistry
from backend.infrastructure.observability import log_event


_RETRYABLE_ERROR_CODES = {"TOOL_TIMEOUT", "TOOL_UNAVAILABLE", "TOOL_EXECUTION_ERROR"}
logger = logging.getLogger(__name__)


class ToolOrchestrator:
    def __init__(self, *, registry: ToolRegistry, chat_client: object) -> None:
        self.registry = registry
        self.chat_client = chat_client

    def run(
        self,
        db_session: Session | None,
        *,
        query: str,
        allowed_tool_names: list[str],
    ) -> ToolOrchestrationOutcome:
        tool_schemas = self.registry.list_schemas(allowed_tool_names) if allowed_tool_names else []
        decision = self.chat_client.decide_tool_call(query=query, tool_schemas=tool_schemas)
        if decision is None:
            return ToolOrchestrationOutcome(tool_calls=[], tool_context=None)

        if decision.tool_name not in allowed_tool_names:
            return ToolOrchestrationOutcome(
                tool_calls=[
                    ToolCallRecord(
                        tool_name=decision.tool_name,
                        arguments=decision.arguments,
                        status="failed",
                        error_code="TOOL_SECURITY_BLOCKED",
                        error_detail="当前问题不允许调用该工具",
                    )
                ],
                tool_context=None,
            )

        try:
            definition = self.registry.get(decision.tool_name)
            result = self._execute_with_retry(
                definition=definition,
                db_session=db_session,
                arguments=decision.arguments,
            )
            return ToolOrchestrationOutcome(
                tool_calls=[result.record],
                tool_context=self._build_tool_context(decision.tool_name, result.output),
            )
        except AppError as exc:
            log_event(
                logger,
                logging.WARNING,
                "tool.call_failed",
                tool_name=decision.tool_name,
                arguments=decision.arguments,
                provider=getattr(definition, "name", None) if "definition" in locals() else None,
                status="failed",
                error_code=exc.code,
            )
            return ToolOrchestrationOutcome(
                tool_calls=[
                    ToolCallRecord(
                        tool_name=decision.tool_name,
                        arguments=decision.arguments,
                        status="failed",
                        error_code=exc.code,
                        error_detail=exc.message,
                    )
                ],
                tool_context=None,
            )

    def _execute_with_retry(self, *, definition, db_session: Session | None, arguments: dict[str, Any]):
        attempts = 0
        while True:
            attempts += 1
            started_at = time.perf_counter()
            try:
                result = definition.handler(db_session, arguments)
                log_event(
                    logger,
                    logging.INFO,
                    "tool.call_completed",
                    tool_name=result.record.tool_name,
                    arguments=result.record.arguments,
                    provider=result.provider,
                    status=result.record.status,
                    latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
                    error_code=result.record.error_code,
                )
                return result
            except AppError as exc:
                log_event(
                    logger,
                    logging.WARNING,
                    "tool.call_attempt_failed",
                    tool_name=definition.name,
                    arguments=arguments,
                    provider=getattr(getattr(definition, "handler", None), "__qualname__", None),
                    status="failed",
                    latency_ms=round((time.perf_counter() - started_at) * 1000, 2),
                    error_code=exc.code,
                )
                if exc.code in _RETRYABLE_ERROR_CODES and attempts < 2:
                    continue
                raise

    def _build_tool_context(self, tool_name: str, output: dict[str, Any]) -> str:
        return f"工具：{tool_name}\n结果：{json.dumps(output, ensure_ascii=False)}"
