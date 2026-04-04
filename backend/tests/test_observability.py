from __future__ import annotations

import logging

import pytest

from backend.app.models import Session as ChatSession
from backend.app.services import document_service as document_service_module
from backend.app.services.chat_service import ChatService
from backend.infrastructure.observability import reset_request_id, set_request_id
from backend.tests.support import create_initialized_test_client


def patch_document_queue(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        document_service_module,
        "create_redis_client",
        lambda redis_url: {"redis_url": redis_url},
    )
    monkeypatch.setattr(
        document_service_module,
        "create_queue",
        lambda redis_client, queue_name=document_service_module.DEFAULT_QUEUE_NAME: {
            "redis_client": redis_client,
            "queue_name": queue_name,
        },
    )
    monkeypatch.setattr(
        document_service_module,
        "enqueue_callable",
        lambda queue, func, *args: type("Job", (), {"id": "job-123"})(),
    )


def test_health_endpoint_sets_request_id_header_and_emits_request_logs(caplog: pytest.LogCaptureFixture) -> None:
    with create_initialized_test_client() as (client, _, _):
        with caplog.at_level(logging.INFO):
            response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    messages = "\n".join(record.message for record in caplog.records)
    assert '"event": "request.started"' in messages
    assert '"event": "request.completed"' in messages
    assert '"request_id":' in messages


def test_document_upload_emits_structured_log(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    patch_document_queue(monkeypatch)

    with create_initialized_test_client() as (client, _, _):
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/api/documents/upload",
                files={"file": ("demo.txt", b"hello world", "text/plain")},
            )

    assert response.status_code == 200
    messages = "\n".join(record.message for record in caplog.records)
    assert '"event": "document.upload_enqueued"' in messages
    assert '"document_id":' in messages
    assert '"task_id":' in messages
    assert '"request_id":' in messages


class FakeQAService:
    def ask(self, db_session, *, query: str):
        return type("Result", (), {"answer": f"回答：{query}", "citations": []})()


def test_chat_query_emits_session_log(caplog: pytest.LogCaptureFixture) -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            session = ChatSession(title="新会话")
            db_session.add(session)
            db_session.commit()
            db_session.refresh(session)
            session_id = session.id

        token = set_request_id("req-chat-test")
        try:
            with client.app.state.db_session_factory() as db_session:
                with caplog.at_level(logging.INFO):
                    qa_result, user_message, assistant_message = ChatService(
                        qa_service=FakeQAService()
                    ).query(db_session, session_id=session_id, query="请总结")
        finally:
            reset_request_id(token)

    assert qa_result.answer == "回答：请总结"
    assert user_message.session_id == session_id
    assert assistant_message.session_id == session_id
    messages = "\n".join(record.message for record in caplog.records)
    assert '"event": "chat.query_completed"' in messages
    assert f'"session_id": "{session_id}"' in messages
    assert '"request_id": "req-chat-test"' in messages
