from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

from backend.api.deps.database import get_db_session
from backend.api.schemas.documents import DocumentDetailData, UploadDocumentData
from backend.api.schemas.response import success_response
from backend.api.schemas.tags import (
    AddDocumentTagRequest,
    BatchDeleteDocumentsRequest,
    BatchTagDocumentsRequest,
    DocumentPreviewChunk,
    SetDocumentTagsRequest,
    TagData,
)
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.services.document_preview_service import get_document_preview
from backend.app.services.document_service import create_document_upload, delete_document, get_document_detail
from backend.app.services.tag_service import (
    add_document_tag,
    get_document_tags,
    remove_document_tag,
    set_document_tags,
)


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(
    search: str | None = Query(default=None),
    tags: str | None = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    db_session: Session = Depends(get_db_session),
) -> dict:
    tag_ids = [int(tag_id.strip()) for tag_id in tags.split(",")] if tags else None
    documents = DocumentRepository(db_session).list_documents(
        search=search,
        tag_ids=tag_ids,
        sort_by=sort,
        order=order,
    )
    return success_response(
        message="获取文档列表成功",
        data=[
            {
                "id": document.id,
                "name": document.name,
                "file_type": document.file_type,
                "status": document.status,
                "storage_path": document.storage_path,
                "graph_status": document.graph_status,
                "graph_relation_count": document.graph_relation_count,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
            }
            for document in documents
        ],
    )


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


@router.post("/batch-upload")
async def batch_upload_documents(
    request: Request,
    files: list[UploadFile] = File(...),
    db_session: Session = Depends(get_db_session),
) -> dict:
    results = []
    for file in files:
        content = await file.read()
        document, task = create_document_upload(
            db_session,
            settings=request.app.state.settings,
            filename=file.filename,
            content=content,
        )
        results.append(
            UploadDocumentData(document_id=document.id, task_id=task.id).model_dump()
        )
    return success_response(message="批量上传成功", data=results)


@router.post("/batch-delete")
def batch_delete_documents(
    request: Request,
    payload: BatchDeleteDocumentsRequest,
    db_session: Session = Depends(get_db_session),
) -> dict:
    for document_id in payload.document_ids:
        delete_document(db_session, document_id, settings=request.app.state.settings)
    return success_response(message="批量删除成功")


@router.post("/batch-tag")
def batch_tag_documents(
    payload: BatchTagDocumentsRequest,
    db_session: Session = Depends(get_db_session),
) -> dict:
    for document_id in payload.document_ids:
        set_document_tags(db_session, document_id, payload.tag_ids)
    return success_response(message="批量打标签成功")


@router.get("/{document_id}")
def get_document(
    document_id: str,
    db_session: Session = Depends(get_db_session),
) -> dict:
    document, visual_asset_count = get_document_detail(db_session, document_id)
    return success_response(
        message="获取文档详情成功",
        data=DocumentDetailData(
            id=document.id,
            name=document.name,
            file_type=document.file_type,
            status=document.status,
            storage_path=document.storage_path,
            has_visual_assets=visual_asset_count > 0,
            visual_asset_count=visual_asset_count,
            has_graph=document.graph_relation_count > 0,
            graph_status=document.graph_status,
            graph_relation_count=document.graph_relation_count,
            created_at=document.created_at.isoformat(),
            updated_at=document.updated_at.isoformat(),
        ).model_dump(),
    )


@router.delete("/{document_id}")
def remove_document(
    request: Request,
    document_id: str,
    db_session: Session = Depends(get_db_session),
) -> dict:
    delete_document(db_session, document_id, settings=request.app.state.settings)
    return success_response(message="文档删除成功")


@router.post("/{document_id}/tags")
def attach_document_tag(
    document_id: str,
    payload: AddDocumentTagRequest,
    db_session: Session = Depends(get_db_session),
) -> dict:
    add_document_tag(db_session, document_id, payload.tag_id)
    return success_response(message="添加文档标签成功")


@router.delete("/{document_id}/tags/{tag_id}")
def detach_document_tag(
    document_id: str,
    tag_id: int,
    db_session: Session = Depends(get_db_session),
) -> dict:
    remove_document_tag(db_session, document_id, tag_id)
    return success_response(message="移除文档标签成功")


@router.put("/{document_id}/tags")
def replace_document_tags(
    document_id: str,
    payload: SetDocumentTagsRequest,
    db_session: Session = Depends(get_db_session),
) -> dict:
    set_document_tags(db_session, document_id, payload.tag_ids)
    return success_response(message="设置文档标签成功")


@router.get("/{document_id}/tags")
def list_document_tags(
    document_id: str,
    db_session: Session = Depends(get_db_session),
) -> dict:
    tags = get_document_tags(db_session, document_id)
    return success_response(
        message="获取文档标签成功",
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


@router.get("/{document_id}/preview")
def preview_document(
    document_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    db_session: Session = Depends(get_db_session),
) -> dict:
    preview_chunks = get_document_preview(db_session, document_id, limit=limit)
    return success_response(
        message="获取文档预览成功",
        data=[DocumentPreviewChunk(**chunk).model_dump() for chunk in preview_chunks],
    )
