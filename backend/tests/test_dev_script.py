from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEV_SCRIPT = PROJECT_ROOT / "scripts" / "dev.ps1"
PID_ROOT = PROJECT_ROOT / ".dev" / "pids"


class _TestHandler(BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, str, bytes]] = {}

    def do_GET(self) -> None:  # noqa: N802
        status_code, content_type, body = self.routes.get(
            self.path,
            (404, "text/plain; charset=utf-8", b"not found"),
        )
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


class LocalHttpServer:
    def __init__(self, routes: dict[str, tuple[int, str, bytes]]) -> None:
        handler_class = type("DevScriptHandler", (_TestHandler,), {"routes": routes})
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def start(self) -> None:
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _write_pid(name: str, pid: int | None) -> None:
    PID_ROOT.mkdir(parents=True, exist_ok=True)
    pid_path = PID_ROOT / f"{name}.pid"
    if pid is None:
        if pid_path.exists():
            pid_path.unlink()
        return
    pid_path.write_text(str(pid), encoding="utf-8")


def _cleanup_pid_files() -> None:
    for service in ("backend", "frontend", "worker"):
        _write_pid(service, None)


def _run_dev_command(command: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(DEV_SCRIPT),
            command,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=20,
    )


def _reserve_running_process() -> subprocess.Popen[str]:
    return subprocess.Popen(
        ["powershell", "-Command", "Start-Sleep -Seconds 20"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def test_acceptance_succeeds_when_optional_neo4j_is_degraded() -> None:
    backend_payload = {
        "success": True,
        "message": "ok",
        "data": {"status": "ok"},
    }
    ready_payload = {
        "success": True,
        "message": "ready",
        "data": {
            "status": "degraded",
            "ready": True,
            "degraded": True,
            "components": [
                {"name": "database", "label": "PostgreSQL", "status": "ready", "required": True},
                {"name": "redis", "label": "Redis", "status": "ready", "required": True},
                {"name": "storage", "label": "文件存储", "status": "ready", "required": True},
                {
                    "name": "neo4j",
                    "label": "Neo4j",
                    "status": "failed",
                    "required": False,
                    "detail": "bolt connection failed",
                },
            ],
        },
    }
    backend_server = LocalHttpServer(
        {
            "/api/health": (200, "application/json; charset=utf-8", _json_bytes(backend_payload)),
            "/api/ready": (200, "application/json; charset=utf-8", _json_bytes(ready_payload)),
        }
    )
    frontend_server = LocalHttpServer(
        {"/": (200, "text/html; charset=utf-8", b"<html><body>frontend ok</body></html>")}
    )
    worker_process = _reserve_running_process()

    try:
        backend_server.start()
        frontend_server.start()
        _cleanup_pid_files()
        _write_pid("worker", worker_process.pid)

        result = _run_dev_command(
            "acceptance",
            {
                "RAG_DEV_BACKEND_URL": backend_server.url,
                "RAG_DEV_FRONTEND_URL": frontend_server.url,
            },
        )
    finally:
        worker_process.terminate()
        worker_process.wait(timeout=10)
        backend_server.close()
        frontend_server.close()
        _cleanup_pid_files()

    assert result.returncode == 0, result.stderr
    assert "acceptance OK" in result.stdout
    assert "Neo4j" in result.stdout
    assert "WARN" in result.stdout


def test_acceptance_fails_when_required_readiness_component_is_not_ready() -> None:
    backend_payload = {
        "success": True,
        "message": "ok",
        "data": {"status": "ok"},
    }
    ready_payload = {
        "success": True,
        "message": "not ready",
        "data": {
            "status": "not_ready",
            "ready": False,
            "degraded": False,
            "components": [
                {
                    "name": "database",
                    "label": "PostgreSQL",
                    "status": "failed",
                    "required": True,
                    "detail": "connection refused",
                },
                {"name": "redis", "label": "Redis", "status": "ready", "required": True},
            ],
        },
    }
    backend_server = LocalHttpServer(
        {
            "/api/health": (200, "application/json; charset=utf-8", _json_bytes(backend_payload)),
            "/api/ready": (503, "application/json; charset=utf-8", _json_bytes(ready_payload)),
        }
    )
    frontend_server = LocalHttpServer(
        {"/": (200, "text/html; charset=utf-8", b"<html><body>frontend ok</body></html>")}
    )
    worker_process = _reserve_running_process()

    try:
        backend_server.start()
        frontend_server.start()
        _cleanup_pid_files()
        _write_pid("worker", worker_process.pid)

        result = _run_dev_command(
            "acceptance",
            {
                "RAG_DEV_BACKEND_URL": backend_server.url,
                "RAG_DEV_FRONTEND_URL": frontend_server.url,
            },
        )
    finally:
        worker_process.terminate()
        worker_process.wait(timeout=10)
        backend_server.close()
        frontend_server.close()
        _cleanup_pid_files()

    assert result.returncode != 0
    assert "acceptance FAIL" in result.stderr
    assert "PostgreSQL" in result.stdout
    assert "connection refused" in result.stdout
