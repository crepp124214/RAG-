from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps.database import get_db_session
from backend.api.schemas.documents import TaskDetailData
from backend.api.schemas.response import success_response
from backend.app.services.document_service import get_task_detail


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
def get_task(
    task_id: str,
    db_session: Session = Depends(get_db_session),
) -> dict:
    task = get_task_detail(db_session, task_id)
    return success_response(
        message="获取任务详情成功",
        data=TaskDetailData(
            id=task.id,
            document_id=task.document_id,
            task_type=task.task_type,
            status=task.status,
            error_message=task.error_message,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        ).model_dump(),
    )
