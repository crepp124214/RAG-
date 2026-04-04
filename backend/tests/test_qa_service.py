from __future__ import annotations

from backend.app.services.qa_service import KnowledgeBaseQAService, NO_HIT_MESSAGE
from backend.app.services.retrieval_service import RetrievedChunk


class FakeRetrievalService:
    def __init__(self, citations: list[RetrievedChunk]) -> None:
        self.citations = citations

    def retrieve(self, db_session, *, query: str) -> list[RetrievedChunk]:
        return self.citations


class FakeChatClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return "基于知识库的回答"


def test_ask_returns_no_hit_message_when_retrieval_is_empty() -> None:
    chat_client = FakeChatClient()
    service = KnowledgeBaseQAService(
        retrieval_service=FakeRetrievalService([]),
        chat_client=chat_client,
    )

    result = service.ask(None, query="没有命中")

    assert result.answer == NO_HIT_MESSAGE
    assert result.citations == []
    assert chat_client.calls == []


def test_ask_uses_retrieved_chunks_to_build_context() -> None:
    citations = [
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="demo.txt",
            chunk_index=0,
            content="第一段内容",
            page_number=2,
            score=0.98,
        )
    ]
    chat_client = FakeChatClient()
    service = KnowledgeBaseQAService(
        retrieval_service=FakeRetrievalService(citations),
        chat_client=chat_client,
    )

    result = service.ask(None, query="请总结")

    assert result.answer == "基于知识库的回答"
    assert result.citations == citations
    assert len(chat_client.calls) == 1
    assert "demo.txt" in chat_client.calls[0]["user_prompt"]
    assert "第一段内容" in chat_client.calls[0]["user_prompt"]
