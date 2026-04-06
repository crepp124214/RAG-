from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.models import Document, Task
from backend.app.orchestrators.document_ingestion import DocumentIngestionOrchestrator
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.app.tools.base import ToolCallDecision
from backend.infrastructure.llm.acceptance_clients import AcceptanceChatClient
from backend.infrastructure.llm import create_embedding_client
from backend.tests.support import create_initialized_test_client


def _create_document_with_task(session_factory, storage_path: Path) -> tuple[str, str]:
    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="txt",
            status="UPLOADED",
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.flush()

        task = Task(
            document_id=document.id,
            task_type="INGESTION",
            status="UPLOADED",
        )
        db_session.add(task)
        db_session.commit()
        return document.id, task.id


def _ingest_document(
    session_factory,
    settings,
    storage_path: Path,
) -> tuple[str, str]:
    document_id, task_id = _create_document_with_task(session_factory, storage_path)
    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=DocumentParserService(),
        chunking_service=DocumentChunkingService(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ),
        embedding_client=create_embedding_client(settings),
    )
    result = orchestrator.process(document_id=document_id, task_id=task_id)
    assert result["status"] == "READY"
    return document_id, task_id


def _extract_sse_events(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in body.strip().split("\n\n"):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        event_line = next((line for line in lines if line.startswith("event:")), None)
        data_line = next((line for line in lines if line.startswith("data:")), None)
        if event_line is None or data_line is None:
            continue

        event_name = event_line[len("event:") :].strip()
        payload = json.loads(data_line[len("data:") :].strip())
        events.append((event_name, payload))
    return events


def _create_acceptance_client(*, overrides: dict[str, str] | None = None):
    merged_overrides = {"LLM_MODE": "acceptance"}
    if overrides:
        merged_overrides.update(overrides)
    return create_initialized_test_client(overrides=merged_overrides)


def test_acceptance_mode_query_triggers_web_search() -> None:
    with _create_acceptance_client() as (client, temp_dir, settings):
        storage_path = temp_dir / "demo.txt"
        storage_path.write_text(
            "第一段：系统支持今天最新的搜索。\n第二段：系统支持知识库引用回答。",
            encoding="utf-8",
        )
        _ingest_document(client.app.state.db_session_factory, settings, storage_path)

        response = client.post("/api/chat/sessions")
        session_id = response.json()["data"]["session_id"]
        response = client.post(
            "/api/chat/query",
            json={"session_id": session_id, "query": "今天最新消息是什么"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["tool_calls"][0]["tool_name"] == "web_search"
    assert payload["data"]["tool_calls"][0]["status"] == "success"
    assert payload["data"]["tool_calls"][0]["arguments"]["query"] == "今天最新消息是什么"
    assert payload["data"]["tool_calls"][0]["arguments"]["top_k"] == 5
    assert payload["data"]["tool_calls"][0]["result_summary"] == "命中 5 条搜索结果"
    assert payload["data"]["answer"].startswith("【验收模式】")


def test_acceptance_mode_query_triggers_document_lookup_content() -> None:
    with _create_acceptance_client() as (client, temp_dir, settings):
        storage_path = temp_dir / "demo.txt"
        storage_path.write_text(
            "第一段：系统支持上传文档。\n第二段：这一页提到了验收模式内容查询。\n第三段：系统支持任务状态查询。",
            encoding="utf-8",
        )
        _ingest_document(client.app.state.db_session_factory, settings, storage_path)

        response = client.post("/api/chat/sessions")
        session_id = response.json()["data"]["session_id"]
        response = client.post(
            "/api/chat/query",
            json={"session_id": session_id, "query": "文档 验收模式"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["tool_calls"][0]["tool_name"] == "document_lookup"
    assert payload["data"]["tool_calls"][0]["status"] == "success"
    assert payload["data"]["tool_calls"][0]["arguments"]["lookup_type"] == "content"
    assert payload["data"]["tool_calls"][0]["result_summary"] == "命中 1 个文档片段"
    assert payload["data"]["citations"]
    assert payload["data"]["answer"].startswith("【验收模式】")


def test_acceptance_mode_query_triggers_document_lookup_status() -> None:
    with _create_acceptance_client() as (client, temp_dir, settings):
        storage_path = temp_dir / "demo.txt"
        storage_path.write_text(
            "第一段：系统支持上传文档。\n第二段：这一页提到了验收模式状态查询。\n第三段：系统支持任务状态查询。",
            encoding="utf-8",
        )
        document_id, _ = _ingest_document(client.app.state.db_session_factory, settings, storage_path)

        original_decide = AcceptanceChatClient.decide_tool_call

        def patched_decide(self, *, query: str, tool_schemas: list[dict[str, object]]):
            decision = original_decide(self, query=query, tool_schemas=tool_schemas)
            if (
                decision is not None
                and decision.tool_name == "document_lookup"
                and "状态" in query
            ):
                return ToolCallDecision(
                    tool_name="document_lookup",
                    arguments={"lookup_type": "status", "document_id": document_id},
                )
            return decision

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(AcceptanceChatClient, "decide_tool_call", patched_decide)
        try:
            response = client.post("/api/chat/sessions")
            session_id = response.json()["data"]["session_id"]
            response = client.post(
                "/api/chat/query",
                json={"session_id": session_id, "query": "请查询这份文档状态"},
            )
        finally:
            monkeypatch.undo()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    tool_call = payload["data"]["tool_calls"][0]
    assert tool_call["tool_name"] == "document_lookup"
    assert tool_call["status"] == "success"
    assert tool_call["arguments"]["lookup_type"] == "status"
    assert tool_call["arguments"]["document_id"] == document_id
    assert tool_call["result_summary"] == "已返回文档/任务状态"
    assert payload["data"]["answer"].startswith("【验收模式】")


def test_acceptance_mode_query_without_tool_keeps_rag_path() -> None:
    with _create_acceptance_client() as (client, temp_dir, settings):
        storage_path = temp_dir / "demo.txt"
        storage_path.write_text(
            "第一段：系统支持上传文档。\n第二段：系统支持引用回答。\n第三段：系统支持任务状态查询。",
            encoding="utf-8",
        )
        _ingest_document(client.app.state.db_session_factory, settings, storage_path)

        response = client.post("/api/chat/sessions")
        session_id = response.json()["data"]["session_id"]
        response = client.post(
            "/api/chat/query",
            json={"session_id": session_id, "query": "系统支持什么能力"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["tool_calls"] == []
    assert payload["data"]["citations"]
    assert payload["data"]["answer"].startswith("【验收模式】")


def test_acceptance_mode_stream_emits_strict_event_sequence_and_tool_summary() -> None:
    with _create_acceptance_client() as (client, temp_dir, settings):
        storage_path = temp_dir / "demo.txt"
        storage_path.write_text(
            "第一段：系统支持今天最新消息查询。\n第二段：系统支持知识库引用回答。",
            encoding="utf-8",
        )
        _ingest_document(client.app.state.db_session_factory, settings, storage_path)

        response = client.post("/api/chat/sessions")
        session_id = response.json()["data"]["session_id"]
        with client.stream(
            "POST",
            "/api/chat/stream",
            json={"session_id": session_id, "query": "今天最新消息是什么"},
        ) as stream_response:
            body = stream_response.read().decode("utf-8")

    assert response.status_code == 200
    assert stream_response.status_code == 200
    assert stream_response.headers["content-type"].startswith("text/event-stream")

    events = _extract_sse_events(body)
    assert [event for event, _ in events[:4]] == [
        "message_start",
        "citation",
        "tool_call",
        "tool_result",
    ]
    assert events[-1][0] == "message_end"
    assert all(event == "token" for event, _ in events[4:-1])
    assert events[2][1]["tool_name"] == "web_search"
    assert events[3][1]["status"] == "success"
    assert events[-1][1]["tool_calls"] == [events[3][1]]
