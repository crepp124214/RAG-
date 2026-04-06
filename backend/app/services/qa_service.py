from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.app.services.retrieval_service import RetrievalService, RetrievedChunk
from backend.app.tools import ToolOrchestrator, determine_allowed_tools


NO_HIT_MESSAGE = "知识库中暂未找到足够相关的内容，请换个问法或先上传相关文档。"
TOOL_FAILURE_MESSAGE = "本次问题需要工具结果，但工具调用未成功，以下回答未包含实时/工具结果。"
SYSTEM_PROMPT = (
    "你是知识库问答助手。只能基于提供的上下文回答，不要编造不存在的事实。"
    "如果上下文不足，应明确说明。"
)


@dataclass(frozen=True)
class QAResult:
    answer: str
    citations: list[RetrievedChunk]
    tool_calls: list[dict[str, Any]]


@dataclass(frozen=True)
class PreparedQAContext:
    citations: list[RetrievedChunk]
    system_prompt: str | None
    user_prompt: str | None
    fallback_answer: str | None
    tool_calls: list[dict[str, Any]]


class KnowledgeBaseQAService:
    def __init__(
        self,
        *,
        retrieval_service: RetrievalService,
        chat_client: object,
        tool_orchestrator: ToolOrchestrator | None = None,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.chat_client = chat_client
        self.tool_orchestrator = tool_orchestrator

    def ask(self, db_session: Session, *, query: str) -> QAResult:
        prepared = self.prepare(db_session, query=query)
        if prepared.fallback_answer is not None:
            return QAResult(
                answer=prepared.fallback_answer,
                citations=prepared.citations,
                tool_calls=prepared.tool_calls,
            )

        answer = self.chat_client.generate(
            system_prompt=prepared.system_prompt or SYSTEM_PROMPT,
            user_prompt=prepared.user_prompt or "",
        )
        return QAResult(answer=answer, citations=prepared.citations, tool_calls=prepared.tool_calls)

    def stream_ask(
        self,
        db_session: Session,
        *,
        query: str,
    ) -> tuple[list[RetrievedChunk], list[dict[str, Any]], Iterator[str]]:
        prepared = self.prepare(db_session, query=query)
        if prepared.fallback_answer is not None:
            return prepared.citations, prepared.tool_calls, iter([prepared.fallback_answer])

        return prepared.citations, prepared.tool_calls, self.chat_client.stream_generate(
            system_prompt=prepared.system_prompt or SYSTEM_PROMPT,
            user_prompt=prepared.user_prompt or "",
        )

    def prepare(self, db_session: Session, *, query: str) -> PreparedQAContext:
        citations = self.retrieval_service.retrieve(db_session, query=query)
        allowed_tools = determine_allowed_tools(query)
        tool_outcome = (
            self.tool_orchestrator.run(db_session, query=query, allowed_tool_names=allowed_tools)
            if self.tool_orchestrator is not None
            else None
        )
        tool_calls = [record.to_dict() for record in tool_outcome.tool_calls] if tool_outcome else []

        if not citations and tool_outcome is None:
            return PreparedQAContext(
                citations=[],
                system_prompt=None,
                user_prompt=None,
                fallback_answer=NO_HIT_MESSAGE,
                tool_calls=[],
            )

        if tool_outcome and tool_outcome.tool_calls and tool_outcome.tool_calls[0].status == "failed":
            return PreparedQAContext(
                citations=citations,
                system_prompt=None,
                user_prompt=None,
                fallback_answer=TOOL_FAILURE_MESSAGE,
                tool_calls=tool_calls,
            )

        return PreparedQAContext(
            citations=citations,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=self._build_prompt(
                query=query,
                citations=citations,
                tool_context=tool_outcome.tool_context if tool_outcome else None,
            ),
            fallback_answer=None,
            tool_calls=tool_calls,
        )

    def _build_context(self, citations: list[RetrievedChunk]) -> str:
        lines: list[str] = []
        for index, citation in enumerate(citations, start=1):
            location = f"第 {citation.page_number} 页" if citation.page_number is not None else "页码未知"
            if citation.source_type == "graph":
                source_hint = "图谱关系"
            elif citation.source_type != "text":
                source_hint = "视觉内容"
            else:
                source_hint = "文本内容"
            asset_hint = f"；标记：{citation.asset_label}" if citation.asset_label else ""
            graph_hint = f"；关系：{citation.entity_path}" if citation.entity_path else ""
            lines.append(
                f"[{index}] 文档：{citation.document_name}；类型：{source_hint}；位置：{location}{asset_hint}{graph_hint}；内容：{citation.content}"
            )
        return "\n".join(lines)

    def _build_prompt(
        self,
        *,
        query: str,
        citations: list[RetrievedChunk],
        tool_context: str | None,
    ) -> str:
        parts = [f"用户问题：{query}"]
        if citations:
            parts.append(f"可用上下文：\n{self._build_context(citations)}")
        if tool_context:
            parts.append(f"工具结果：\n{tool_context}")
        return "\n\n".join(parts)
