from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class SmokeConfig:
    backend_url: str
    poll_interval: float
    max_polls: int
    query: str
    document_content: str


class SmokeFlowError(RuntimeError):
    pass


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _request_json(
    *,
    method: str,
    url: str,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    req = request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)

    try:
        with request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SmokeFlowError(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise SmokeFlowError(f"{method} {url} failed: {exc.reason}") from exc

    if not payload.get("success", False):
        raise SmokeFlowError(f"{method} {url} returned unsuccessful payload: {payload}")

    return payload


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _request_json(
        method="POST",
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


def _build_multipart_file_payload(*, filename: str, content: str) -> tuple[bytes, str]:
    boundary = f"----SmokeFlowBoundary{uuid.uuid4().hex}"
    file_bytes = content.encode("utf-8")
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: text/plain\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def _upload_document(base_url: str, content: str) -> tuple[str, str]:
    body, boundary = _build_multipart_file_payload(filename="smoke-flow.txt", content=content)
    payload = _request_json(
        method="POST",
        url=f"{base_url}/api/documents/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    data = payload["data"]
    return data["document_id"], data["task_id"]


def _create_session(base_url: str) -> str:
    payload = _request_json(method="POST", url=f"{base_url}/api/chat/sessions")
    return payload["data"]["session_id"]


def _poll_task_until_ready(base_url: str, task_id: str, *, poll_interval: float, max_polls: int) -> None:
    last_status = "UNKNOWN"
    for _ in range(max_polls):
        payload = _request_json(method="GET", url=f"{base_url}/api/tasks/{task_id}")
        data = payload["data"]
        last_status = data["status"]
        if last_status == "READY":
            return
        if last_status == "FAILED":
            error_message = data.get("error_message") or "unknown error"
            raise SmokeFlowError(f"Task {task_id} entered FAILED state: {error_message}")
        time.sleep(poll_interval)

    raise SmokeFlowError(f"Task {task_id} did not become READY within {max_polls} polls (last_status={last_status})")


def _query_chat(base_url: str, session_id: str, query: str, document_id: str) -> None:
    payload = _post_json(
        f"{base_url}/api/chat/query",
        {"session_id": session_id, "query": query},
    )
    data = payload["data"]
    answer = (data.get("answer") or "").strip()
    citations = data.get("citations") or []

    if not answer:
        raise SmokeFlowError("Chat query returned empty answer")
    if not citations:
        raise SmokeFlowError("Chat query returned no citations")
    if not any(citation.get("document_id") == document_id for citation in citations):
        raise SmokeFlowError(f"Chat citations did not reference uploaded document {document_id}")


def _delete_document(base_url: str, document_id: str) -> None:
    _request_json(method="DELETE", url=f"{base_url}/api/documents/{document_id}")


def run_smoke_flow(config: SmokeConfig) -> None:
    base_url = _normalize_base_url(config.backend_url)
    document_id: str | None = None

    try:
        document_id, task_id = _upload_document(base_url, config.document_content)
        _poll_task_until_ready(
            base_url,
            task_id,
            poll_interval=config.poll_interval,
            max_polls=config.max_polls,
        )
        session_id = _create_session(base_url)
        _query_chat(base_url, session_id, config.query, document_id)
    finally:
        if document_id:
            try:
                _delete_document(base_url, document_id)
            except SmokeFlowError as exc:
                print(f"smoke-flow WARN cleanup failed: {exc}", file=sys.stderr)

    print("smoke-flow OK: upload, readiness polling, chat query, citations, and cleanup passed.")


def parse_args(argv: list[str] | None = None) -> SmokeConfig:
    parser = argparse.ArgumentParser(description="Run a minimal end-to-end smoke flow against the live backend.")
    parser.add_argument("--backend-url", required=True, help="Backend base URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between task polls")
    parser.add_argument("--max-polls", type=int, default=30, help="Maximum number of task polls before timeout")
    parser.add_argument("--query", default="请概括这份文档的主要内容", help="Smoke query to ask after ingestion")
    parser.add_argument(
        "--document-content",
        default="这份文档提到了验收链路，并用于第五阶段主链路 smoke 验证。",
        help="Inline UTF-8 content for the temporary smoke test document",
    )
    args = parser.parse_args(argv)
    return SmokeConfig(
        backend_url=args.backend_url,
        poll_interval=args.poll_interval,
        max_polls=args.max_polls,
        query=args.query,
        document_content=args.document_content,
    )


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    try:
        run_smoke_flow(config)
    except SmokeFlowError as exc:
        print(f"smoke-flow FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
