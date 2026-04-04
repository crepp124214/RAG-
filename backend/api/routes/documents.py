from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from backend.api.deps.database import get_db_session
from backend.api.schemas.documents import DocumentDetailData, UploadDocumentData
from backend.api.schemas.response import success_response
from backend.app.services.document_service import create_document_upload, delete_document, get_document_detail


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db_session: Session = Depends(get_db_session),
) -> dict:
    content = await file.read()
    document, task = create_document_upload(
        db_session,
        settings=request.app.state.settings,
        filename=file.filename,
        content=content,
    )
    return success_response(
        message="文档上传成功",
        data=UploadDocumentData(
            document_id=document.id,
            task_id=task.id,
        ).model_dump(),
    )


@router.get("/{document_id}")
def get_document(
    document_id: str,
    db_session: Session = Depends(get_db_session),
) -> dict:
    document = get_document_detail(db_session, document_id)
    return success_response(
        message="获取文档详情成功",
        data=DocumentDetailData(
            id=document.id,
            name=document.name,
            file_type=document.file_type,
            status=document.status,
            storage_path=document.storage_path,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat(),
        ).model_dump(),
    )


@router.delete("/{document_id}")
def remove_document(
    document_id: str,
    db_session: Session = Depends(get_db_session),
) -> dict:
    delete_document(db_session, document_id)
    return success_response(message="文档删除成功")
