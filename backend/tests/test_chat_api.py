from __future__ import annotations

import json

from backend.api.routes import chat as chat_route_module
from backend.app.services.qa_service import QAResult
from backend.app.services.retrieval_service import RetrievedChunk
from backend.tests.support import create_initialized_test_client


class FakeChatService:
    def __init__(self) -> None:
        self.created_sessions = []
        self.queries = []

    def create_session(self, db_session, *, title: str = "新会话"):
        from backend.app.models import Session as ChatSession

        session = ChatSession(id="session-1", title=title)
        session.created_at = session.updated_at  # type: ignore[assignment]
        self.created_sessions.append(title)
        return session

    def list_sessions(self, db_session):
        from backend.app.models import Session as ChatSession
        from backend.app.models.base import utcnow

        now = utcnow()
        first = ChatSession(id="session-1", title="最近会话")
        first.created_at = now  # type: ignore[assignment]
        first.updated_at = now  # type: ignore[assignment]
        return [first]

    def list_messages(self, db_session, *, session_id: str):
        from backend.app.models import Message
        from backend.app.models.base import utcnow

        now = utcnow()
        message = Message(
            id="message-1",
            session_id=session_id,
            role="assistant",
            content="你好",
            citations=[
                {
                    "document_id": "doc-1",
                    "document_name": "demo.txt",
                    "chunk_id": "chunk-1",
                    "content": "片段",
                    "page_number": 1,
                    "source_type": "text",
                    "asset_label": None,
                    "preview_available": False,
                }
            ],
            tool_calls=[
                {
                    "tool_name": "web_search",
                    "arguments": {"query": "你好"},
                    "status": "success",
                    "result_summary": "命中 1 条搜索结果",
                    "error_code": None,
                    "error_detail": None,
                }
            ],
        )
        message.created_at = now  # type: ignore[assignment]
        message.updated_at = now  # type: ignore[assignment]
        return [message]

    def query(self, db_session, *, session_id: str, query: str):
        from backend.app.models import Message
        from backend.app.models.base import utcnow

        self.queries.append({"session_id": session_id, "query": query})
        now = utcnow()
        user_message = Message(id="user-1", session_id=session_id, role="user", content=query)
        assistant_message = Message(id="assistant-1", session_id=session_id, role="assistant", content="这是回答")
        user_message.created_at = now  # type: ignore[assignment]
        user_message.updated_at = now  # type: ignore[assignment]
        assistant_message.created_at = now  # type: ignore[assignment]
        assistant_message.updated_at = now  # type: ignore[assignment]
        result = QAResult(
            answer="这是回答",
            citations=[
                RetrievedChunk(
                    chunk_id="chunk-1",
                    document_id="doc-1",
                    document_name="demo.txt",
                    chunk_index=0,
                    content="片段",
                    page_number=1,
                    source_type="text",
                    asset_label=None,
                    preview_available=False,
                    score=0.9,
                )
            ],
            tool_calls=[
                {
                    "tool_name": "web_search",
                    "arguments": {"query": "请总结"},
                    "status": "success",
                    "result_summary": "命中 1 条搜索结果",
                    "error_code": None,
                    "error_detail": None,
                }
            ],
        )
        return result, user_message, assistant_message

    def stream_query(self, db_session, *, session_id: str, query: str):
        self.queries.append({"session_id": session_id, "query": query})
        yield type("Event", (), {"event": "message_start", "data": {"session_id": session_id}})
        yield type(
            "Event",
            (),
            {
                "event": "citation",
                "data": {
                    "document_id": "doc-1",
                    "document_name": "demo.txt",
                    "chunk_id": "chunk-1",
                    "content": "片段",
                    "page_number": 1,
                    "source_type": "text",
                    "asset_label": None,
                    "preview_available": False,
                },
            },
        )
        yield type(
            "Event",
            (),
            {
                "event": "tool_call",
                "data": {
                    "tool_name": "web_search",
                    "arguments": {"query": query},
                },
            },
        )
        yield type(
            "Event",
            (),
            {
                "event": "tool_result",
                "data": {
                    "tool_name": "web_search",
                    "arguments": {"query": query},
                    "status": "success",
                    "result_summary": "命中 1 条搜索结果",
                    "error_code": None,
                    "error_detail": None,
                },
            },
        )
        yield type("Event", (), {"event": "token", "data": {"content": "流式"}})
        yield type(
            "Event",
            (),
            {
                "event": "message_end",
                "data": {
                    "answer": "流式",
                    "tool_calls": [
                        {
                            "tool_name": "web_search",
                            "arguments": {"query": query},
                            "status": "success",
                            "result_summary": "命中 1 条搜索结果",
                            "error_code": None,
                            "error_detail": None,
                        }
                    ],
                    "user_message_id": "user-1",
                    "assistant_message_id": "assistant-1",
                    "session_id": session_id,
                },
            },
        )


def _parse_sse_body(body: str) -> list[tuple[str, dict[str, object]]]:
    events: list[tuple[str, dict[str, object]]] = []
    for block in body.strip().split("\n\n"):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        event_line = next((line for line in lines if line.startswith("event:")), None)
        data_line = next((line for line in lines if line.startswith("data:")), None)
        if not event_line or not data_line:
            continue

        event_name = event_line[len("event:") :].strip()
        payload = json.loads(data_line[len("data:") :].strip())
        events.append((event_name, payload))
    return events


def test_create_session_endpoint_returns_minimal_payload() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.post("/api/chat/sessions")
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["session_id"] == "session-1"
    assert payload["data"]["title"] == "新会话"


def test_list_sessions_endpoint_returns_recent_sessions() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.get("/api/chat/sessions")
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"][0]["id"] == "session-1"


def test_list_sessions_endpoint_returns_empty_array_when_no_sessions() -> None:
    class EmptyChatService(FakeChatService):
        def list_sessions(self, db_session):
            return []

    fake_service = EmptyChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.get("/api/chat/sessions")
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] == []


def test_list_messages_endpoint_returns_session_messages() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.get("/api/chat/sessions/session-1/messages")
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"][0]["session_id"] == "session-1"
    assert payload["data"][0]["role"] == "assistant"
    assert payload["data"][0]["citations"][0]["document_id"] == "doc-1"
    assert payload["data"][0]["citations"][0]["source_type"] == "text"
    assert payload["data"][0]["tool_calls"][0]["tool_name"] == "web_search"


def test_query_endpoint_returns_answer_and_citations() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.post(
            "/api/chat/query",
            json={"session_id": "session-1", "query": "请总结"},
        )
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["answer"] == "这是回答"
    assert payload["data"]["citations"][0]["document_id"] == "doc-1"
    assert payload["data"]["citations"][0]["source_type"] == "text"
    assert payload["data"]["tool_calls"][0]["tool_name"] == "web_search"
    assert payload["data"]["user_message_id"] == "user-1"
    assert payload["data"]["assistant_message_id"] == "assistant-1"


def test_query_endpoint_rejects_empty_query() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.post(
            "/api/chat/query",
            json={"session_id": "session-1", "query": ""},
        )
        client.app.dependency_overrides.clear()

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"


def test_query_endpoint_rejects_empty_session_id() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.post(
            "/api/chat/query",
            json={"session_id": "", "query": "请总结"},
        )
        client.app.dependency_overrides.clear()

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"


def test_stream_endpoint_returns_sse_events() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        with client.stream(
            "POST",
            "/api/chat/stream",
            json={"session_id": "session-1", "query": "请流式回答"},
        ) as response:
            body = response.read().decode("utf-8")
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse_body(body)
    assert [event for event, _ in events] == [
        "message_start",
        "citation",
        "tool_call",
        "tool_result",
        "token",
        "message_end",
    ]
    assert events[2][1]["tool_name"] == "web_search"
    assert events[3][1]["status"] == "success"
    assert events[1][1]["source_type"] == "text"
    assert events[-1][1]["citations"] == [events[1][1]]
    assert events[-1][1]["tool_calls"] == [events[3][1]]


def test_stream_endpoint_rejects_empty_query() -> None:
    fake_service = FakeChatService()

    with create_initialized_test_client() as (client, _, _):
        client.app.dependency_overrides[chat_route_module.get_chat_service] = lambda: fake_service
        response = client.post(
            "/api/chat/stream",
            json={"session_id": "session-1", "query": ""},
        )
        client.app.dependency_overrides.clear()

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "validation_error"
