from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from backend.app.exceptions import AppError
from backend.app.models import Document, Tag
from backend.app.services.tag_service import (
    add_document_tag,
    create_tag,
    delete_tag,
    get_document_tags,
    list_tags,
    remove_document_tag,
    set_document_tags,
    update_tag,
)
from backend.tests.support import create_initialized_test_client


def test_create_tag() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            tag = create_tag(db_session, name="测试标签", color="#FF0000")
            
            assert tag.id is not None
            assert tag.name == "测试标签"
            assert tag.color == "#FF0000"


def test_create_tag_duplicate_name() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            create_tag(db_session, name="重复标签")
            
            with pytest.raises(AppError) as exc_info:
                create_tag(db_session, name="重复标签")
            
            assert exc_info.value.code == "tag_already_exists"


def test_update_tag() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            tag = create_tag(db_session, name="原标签")
            
            updated_tag = update_tag(db_session, tag.id, name="新标签", color="#00FF00")
            
            assert updated_tag.id == tag.id
            assert updated_tag.name == "新标签"
            assert updated_tag.color == "#00FF00"


def test_update_tag_not_found() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            with pytest.raises(AppError) as exc_info:
                update_tag(db_session, 999, name="不存在")
            
            assert exc_info.value.code == "tag_not_found"


def test_delete_tag() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            tag = create_tag(db_session, name="待删除标签")
            tag_id = tag.id
            
            delete_tag(db_session, tag_id)
            
            deleted_tag = db_session.get(Tag, tag_id)
            assert deleted_tag is None


def test_list_tags() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            create_tag(db_session, name="标签1")
            create_tag(db_session, name="标签2")
            
            tags = list_tags(db_session)
            
            assert len(tags) == 2
            assert tags[0].name in ["标签1", "标签2"]


def test_add_document_tag() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            document = Document(
                name="测试文档.pdf",
                file_type="pdf",
                status="READY",
                storage_path="/test/path.pdf",
            )
            db_session.add(document)
            db_session.commit()
            db_session.refresh(document)
            
            tag = create_tag(db_session, name="文档标签")
            
            add_document_tag(db_session, document.id, tag.id)
            
            document_tags = get_document_tags(db_session, document.id)
            assert len(document_tags) == 1
            assert document_tags[0].id == tag.id


def test_add_document_tag_duplicate() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            document = Document(
                name="测试文档.pdf",
                file_type="pdf",
                status="READY",
                storage_path="/test/path.pdf",
            )
            db_session.add(document)
            db_session.commit()
            db_session.refresh(document)
            
            tag = create_tag(db_session, name="重复标签")
            
            add_document_tag(db_session, document.id, tag.id)
            
            with pytest.raises(AppError) as exc_info:
                add_document_tag(db_session, document.id, tag.id)
            
            assert exc_info.value.code == "tag_already_added"


def test_remove_document_tag() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            document = Document(
                name="测试文档.pdf",
                file_type="pdf",
                status="READY",
                storage_path="/test/path.pdf",
            )
            db_session.add(document)
            db_session.commit()
            db_session.refresh(document)
            
            tag = create_tag(db_session, name="待移除标签")
            add_document_tag(db_session, document.id, tag.id)
            
            remove_document_tag(db_session, document.id, tag.id)
            
            document_tags = get_document_tags(db_session, document.id)
            assert len(document_tags) == 0


def test_set_document_tags() -> None:
    with create_initialized_test_client() as (client, _, _):
        with client.app.state.db_session_factory() as db_session:
            document = Document(
                name="测试文档.pdf",
                file_type="pdf",
                status="READY",
                storage_path="/test/path.pdf",
            )
            db_session.add(document)
            db_session.commit()
            db_session.refresh(document)
            
            tag1 = create_tag(db_session, name="标签1")
            tag2 = create_tag(db_session, name="标签2")
            tag3 = create_tag(db_session, name="标签3")
            
            set_document_tags(db_session, document.id, [tag1.id, tag2.id])
            
            document_tags = get_document_tags(db_session, document.id)
            assert len(document_tags) == 2
            
            set_document_tags(db_session, document.id, [tag3.id])
            
            document_tags = get_document_tags(db_session, document.id)
            assert len(document_tags) == 1
            assert document_tags[0].id == tag3.id
