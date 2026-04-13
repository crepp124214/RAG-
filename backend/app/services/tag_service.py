from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.models.tag import Tag
from backend.app.repositories.document_repository import DocumentRepository
from backend.app.repositories.tag_repository import TagRepository
from backend.infrastructure.observability import log_event


logger = logging.getLogger(__name__)


def create_tag(db_session: Session, *, name: str, color: str = "#409EFF") -> Tag:
    tag_repository = TagRepository(db_session)

    existing_tag = tag_repository.get_by_name(name)
    if existing_tag:
        raise AppError("标签已存在", code="tag_already_exists", status_code=409)

    tag = tag_repository.add(Tag(name=name, color=color))
    db_session.commit()
    db_session.refresh(tag)

    log_event(logger, logging.INFO, "tag.created", tag_id=tag.id, name=tag.name)
    return tag


def update_tag(db_session: Session, tag_id: int, *, name: str | None = None, color: str | None = None) -> Tag:
    tag_repository = TagRepository(db_session)

    tag = tag_repository.get_by_id(tag_id)
    if not tag:
        raise AppError("标签不存在", code="tag_not_found", status_code=404)

    if name is not None:
        existing_tag = tag_repository.get_by_name(name)
        if existing_tag and existing_tag.id != tag_id:
            raise AppError("标签名称已存在", code="tag_name_conflict", status_code=409)
        tag.name = name

    if color is not None:
        tag.color = color

    db_session.commit()
    db_session.refresh(tag)

    log_event(logger, logging.INFO, "tag.updated", tag_id=tag.id, name=tag.name)
    return tag


def delete_tag(db_session: Session, tag_id: int) -> None:
    tag_repository = TagRepository(db_session)

    tag = tag_repository.get_by_id(tag_id)
    if not tag:
        raise AppError("标签不存在", code="tag_not_found", status_code=404)

    tag_repository.delete(tag)
    db_session.commit()

    log_event(logger, logging.INFO, "tag.deleted", tag_id=tag_id)


def list_tags(db_session: Session) -> list[Tag]:
    tag_repository = TagRepository(db_session)
    return tag_repository.list_all()


def add_document_tag(db_session: Session, document_id: str, tag_id: int) -> None:
    document_repository = DocumentRepository(db_session)
    tag_repository = TagRepository(db_session)

    document = document_repository.get_by_id(document_id)
    if not document:
        raise AppError("文档不存在", code="document_not_found", status_code=404)

    tag = tag_repository.get_by_id(tag_id)
    if not tag:
        raise AppError("标签不存在", code="tag_not_found", status_code=404)

    if tag_repository.tag_exists(document_id, tag_id):
        raise AppError("文档已有该标签", code="tag_already_added", status_code=409)

    tag_repository.add_document_tag(document_id, tag_id)
    db_session.commit()

    log_event(logger, logging.INFO, "document.tag_added", document_id=document_id, tag_id=tag_id)


def remove_document_tag(db_session: Session, document_id: str, tag_id: int) -> None:
    document_repository = DocumentRepository(db_session)
    tag_repository = TagRepository(db_session)

    document = document_repository.get_by_id(document_id)
    if not document:
        raise AppError("文档不存在", code="document_not_found", status_code=404)

    tag_repository.remove_document_tag(document_id, tag_id)
    db_session.commit()

    log_event(logger, logging.INFO, "document.tag_removed", document_id=document_id, tag_id=tag_id)


def set_document_tags(db_session: Session, document_id: str, tag_ids: list[int]) -> None:
    document_repository = DocumentRepository(db_session)
    tag_repository = TagRepository(db_session)

    document = document_repository.get_by_id(document_id)
    if not document:
        raise AppError("文档不存在", code="document_not_found", status_code=404)

    for tag_id in tag_ids:
        tag = tag_repository.get_by_id(tag_id)
        if not tag:
            raise AppError(f"标签 {tag_id} 不存在", code="tag_not_found", status_code=404)

    tag_repository.set_document_tags(document_id, tag_ids)
    db_session.commit()

    log_event(logger, logging.INFO, "document.tags_set", document_id=document_id, tag_ids=tag_ids)


def get_document_tags(db_session: Session, document_id: str) -> list[Tag]:
    document_repository = DocumentRepository(db_session)
    tag_repository = TagRepository(db_session)

    document = document_repository.get_by_id(document_id)
    if not document:
        raise AppError("文档不存在", code="document_not_found", status_code=404)

    return tag_repository.get_document_tags(document_id)
