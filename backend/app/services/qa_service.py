from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.services.retrieval_service import RetrievalService, RetrievedChunk


NO_HIT_MESSAGE = "知识库中暂未找到足够相关的内容，请换个问法或先上传相关文档。"
SYSTEM_PROMPT = (
    "你是知识库问答助手。只能基于提供的上下文回答，不要编造不存在的事实。"
    "如果上下文不足，应明确说明。"
)


@dataclass(frozen=True)
class QAResult:
    answer: str
    citations: list[RetrievedChunk]


@dataclass(frozen=True)
class PreparedQAContext:
    citations: list[RetrievedChunk]
    system_prompt: str | None
    user_prompt: str | None
    fallback_answer: str | None


class KnowledgeBaseQAService:
    def __init__(self, *, retrieval_service: RetrievalService, chat_client: object) -> None:
        self.retrieval_service = retrieval_service
        self.chat_client = chat_client

    def ask(self, db_session: Session, *, query: str) -> QAResult:
        prepared = self.prepare(db_session, query=query)
        if prepared.fallback_answer is not None:
            return QAResult(answer=prepared.fallback_answer, citations=prepared.citations)

        answer = self.chat_client.generate(
            system_prompt=prepared.system_prompt or SYSTEM_PROMPT,
            user_prompt=prepared.user_prompt or "",
        )
        return QAResult(answer=answer, citations=prepared.citations)

    def stream_ask(self, db_session: Session, *, query: str) -> tuple[list[RetrievedChunk], Iterator[str]]:
        prepared = self.prepare(db_session, query=query)
        if prepared.fallback_answer is not None:
            return prepared.citations, iter([prepared.fallback_answer])

        return prepared.citations, self.chat_client.stream_generate(
            system_prompt=prepared.system_prompt or SYSTEM_PROMPT,
            user_prompt=prepared.user_prompt or "",
        )

    def prepare(self, db_session: Session, *, query: str) -> PreparedQAContext:
        citations = self.retrieval_service.retrieve(db_session, query=query)
        if not citations:
            return PreparedQAContext(
                citations=[],
                system_prompt=None,
                user_prompt=None,
                fallback_answer=NO_HIT_MESSAGE,
            )

        context = self._build_context(citations)
        return PreparedQAContext(
            citations=citations,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=f"用户问题：{query}\n\n可用上下文：\n{context}",
            fallback_answer=None,
        )

    def _build_context(self, citations: list[RetrievedChunk]) -> str:
        lines: list[str] = []
        for index, citation in enumerate(citations, start=1):
            location = f"第 {citation.page_number} 页" if citation.page_number is not None else "页码未知"
            lines.append(
                f"[{index}] 文档：{citation.document_name}；位置：{location}；内容：{citation.content}"
            )
        return "\n".join(lines)
