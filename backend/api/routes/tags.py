from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps.database import get_db_session
from backend.api.schemas.response import success_response
from backend.api.schemas.tags import (
    CreateTagRequest,
    TagData,
    UpdateTagRequest,
)
from backend.app.services.tag_service import (
    create_tag,
    delete_tag,
    list_tags,
    update_tag,
)


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("")
def get_tags(db_session: Session = Depends(get_db_session)) -> dict:
    tags = list_tags(db_session)
    return success_response(
        message="获取标签列表成功",
        data=[
            TagData(
                id=tag.id,
                name=tag.name,
                color=tag.color,
                created_at=tag.created_at.isoformat(),
                updated_at=tag.updated_at.isoformat(),
            ).model_dump()
            for tag in tags
        ],
    )


@router.post("")
def create_new_tag(
    request: CreateTagRequest,
    db_session: Session = Depends(get_db_session),
) -> dict:
    tag = create_tag(db_session, name=request.name, color=request.color)
    return success_response(
        message="创建标签成功",
        data=TagData(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            created_at=tag.created_at.isoformat(),
            updated_at=tag.updated_at.isoformat(),
        ).model_dump(),
    )


@router.put("/{tag_id}")
def update_existing_tag(
    tag_id: int,
    request: UpdateTagRequest,
    db_session: Session = Depends(get_db_session),
) -> dict:
    tag = update_tag(db_session, tag_id, name=request.name, color=request.color)
    return success_response(
        message="更新标签成功",
        data=TagData(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            created_at=tag.created_at.isoformat(),
            updated_at=tag.updated_at.isoformat(),
        ).model_dump(),
    )


@router.delete("/{tag_id}")
def remove_tag(
    tag_id: int,
    db_session: Session = Depends(get_db_session),
) -> dict:
    delete_tag(db_session, tag_id)
    return success_response(message="删除标签成功")
