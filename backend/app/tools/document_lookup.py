from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.repositories.chunk_repository import ChunkRepository
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.tools.base import ToolCallRecord, ToolDefinition, ToolExecutionResult


class DocumentLookupTool:
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="document_lookup",
            description="查询文档状态、任务状态或文档片段内容。",
            parameters={
                "type": "object",
                "properties": {
                    "lookup_type": {"type": "string", "enum": ["status", "content"]},
                    "document_id": {"type": "string"},
                    "task_id": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["lookup_type"],
            },
            handler=self.execute,
        )

    def execute(self, db_session: Session | None, arguments: dict[str, Any]) -> ToolExecutionResult:
        if db_session is None:
            raise AppError("document_lookup 需要数据库会话", code="TOOL_EXECUTION_ERROR", status_code=500)

        lookup_type = str(arguments.get("lookup_type", "")).strip()
        if lookup_type == "status":
            return self._lookup_status(db_session, arguments)
        if lookup_type == "content":
            return self._lookup_content(db_session, arguments)
        raise AppError("document_lookup 的 lookup_type 非法", code="TOOL_BAD_ARGUMENTS", status_code=400)

    def _lookup_status(self, db_session: Session, arguments: dict[str, Any]) -> ToolExecutionResult:
        document_id = str(arguments.get("document_id", "")).strip()
        task_id = str(arguments.get("task_id", "")).strip()
        if not document_id and not task_id:
            raise AppError(
                "状态查询至少需要 document_id 或 task_id",
                code="TOOL_BAD_ARGUMENTS",
                status_code=400,
            )

        payload: dict[str, Any] = {}
        if document_id:
            document = DocumentRepository(db_session).get_by_id(document_id)
            if document is None:
                raise AppError("文档不存在", code="TOOL_EXECUTION_ERROR", status_code=404)
            payload["document"] = {
                "id": document.id,
                "name": document.name,
                "file_type": document.file_type,
                "status": document.status,
            }

        if task_id:
            task = TaskRepository(db_session).get_by_id(task_id)
            if task is None:
                raise AppError("任务不存在", code="TOOL_EXECUTION_ERROR", status_code=404)
            payload["task"] = {
                "id": task.id,
                "document_id": task.document_id,
                "task_type": task.task_type,
                "status": task.status,
                "error_message": task.error_message,
            }

        return ToolExecutionResult(
            output=payload,
            record=ToolCallRecord(
                tool_name="document_lookup",
                arguments={k: v for k, v in arguments.items() if v is not None},
                status="success",
                result_summary="已返回文档/任务状态",
            ),
            provider="database",
        )

    def _lookup_content(self, db_session: Session, arguments: dict[str, Any]) -> ToolExecutionResult:
        query = str(arguments.get("query", "")).strip()
        document_id = str(arguments.get("document_id", "")).strip() or None
        limit = int(arguments.get("limit", 5) or 5)
        if limit <= 0:
            raise AppError("content 查询的 limit 必须大于 0", code="TOOL_BAD_ARGUMENTS", status_code=400)
        if not query and not document_id:
            raise AppError("content 查询至少需要 query 或 document_id", code="TOOL_BAD_ARGUMENTS", status_code=400)

        matches = ChunkRepository(db_session).search_content(
            query=query,
            document_id=document_id,
            limit=limit,
        )
        return ToolExecutionResult(
            output={"matches": matches},
            record=ToolCallRecord(
                tool_name="document_lookup",
                arguments={k: v for k, v in arguments.items() if v is not None},
                status="success",
                result_summary=f"命中 {len(matches)} 个文档片段",
            ),
            provider="database",
        )
