from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SMOKE_FLOW_SCRIPT = PROJECT_ROOT / "scripts" / "smoke_flow.py"


class _FlowHandler(BaseHTTPRequestHandler):
    state: dict[str, object] = {}

    def _json_response(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/documents/upload":
            self.server.state["upload_called"] = True
            self._json_response(
                200,
                {
                    "success": True,
                    "message": "文档上传成功",
                    "data": {"document_id": "doc-1", "task_id": "task-1"},
                    "error": None,
                },
            )
            return

        if self.path == "/api/chat/sessions":
            self.server.state["session_called"] = True
            self._json_response(
                200,
                {
                    "success": True,
                    "message": "会话创建成功",
                    "data": {"session_id": "session-1", "title": "新会话"},
                    "error": None,
                },
            )
            return

        if self.path == "/api/chat/query":
            self.server.state["query_called"] = True
            self._json_response(
                200,
                {
                    "success": True,
                    "message": "问答成功",
                    "data": {
                        "answer": "文档提到了验收链路。",
                        "citations": [
                            {
                                "document_id": "doc-1",
                                "document_name": "smoke-flow.txt",
                                "chunk_id": "chunk-1",
                                "content": "验收链路",
                                "page_number": 1,
                                "source_type": "text",
                                "asset_label": None,
                                "preview_available": False,
                                "relation_label": None,
                                "entity_path": None,
                            }
                        ],
                        "tool_calls": [],
                        "user_message_id": "u-1",
                        "assistant_message_id": "a-1",
                    },
                    "error": None,
                },
            )
            return

        self._json_response(404, {"success": False, "message": "missing", "data": None, "error": None})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/tasks/task-1":
            poll_count = int(self.server.state.get("task_poll_count", 0)) + 1
            self.server.state["task_poll_count"] = poll_count
            status = self.server.state.get("task_status", "READY")
            if isinstance(status, list):
                index = min(poll_count - 1, len(status) - 1)
                resolved_status = status[index]
            else:
                resolved_status = status
            self._json_response(
                200,
                {
                    "success": True,
                    "message": "获取任务详情成功",
                    "data": {
                        "id": "task-1",
                        "document_id": "doc-1",
                        "task_type": "DOCUMENT_INGESTION",
                        "status": resolved_status,
                        "error_message": "embedding failed" if resolved_status == "FAILED" else None,
                        "created_at": "2026-04-07T00:00:00",
                        "updated_at": "2026-04-07T00:00:01",
                    },
                    "error": None,
                },
            )
            return

        self._json_response(404, {"success": False, "message": "missing", "data": None, "error": None})

    def do_DELETE(self) -> None:  # noqa: N802
        if self.path == "/api/documents/doc-1":
            self.server.state["delete_called"] = True
            self._json_response(
                200,
                {"success": True, "message": "文档删除成功", "data": None, "error": None},
            )
            return

        self._json_response(404, {"success": False, "message": "missing", "data": None, "error": None})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


class FlowServer:
    def __init__(self, state: dict[str, object]) -> None:
        handler_class = type("FlowScriptHandler", (_FlowHandler,), {})
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
        self._server.state = state
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> "FlowServer":
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def _run_smoke_flow(base_url: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SMOKE_FLOW_SCRIPT),
            "--backend-url",
            base_url,
            "--poll-interval",
            "0.01",
            "--max-polls",
            "3",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=20,
    )


def test_smoke_flow_script_succeeds_on_minimal_happy_path() -> None:
    state: dict[str, object] = {"task_status": ["PARSING", "READY"]}

    with FlowServer(state) as server:
        completed = _run_smoke_flow(server.base_url)

    assert completed.returncode == 0, completed.stderr
    assert "smoke-flow OK" in completed.stdout
    assert state["upload_called"] is True
    assert state["session_called"] is True
    assert state["query_called"] is True
    assert state["delete_called"] is True


def test_smoke_flow_script_fails_when_task_enters_failed_state() -> None:
    state: dict[str, object] = {"task_status": ["PARSING", "FAILED"]}

    with FlowServer(state) as server:
        completed = _run_smoke_flow(server.base_url)

    assert completed.returncode != 0
    assert "FAILED" in completed.stderr
    assert state["upload_called"] is True
    assert state["delete_called"] is True
