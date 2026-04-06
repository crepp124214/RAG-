from __future__ import annotations

from pathlib import Path

import fitz

from backend.app.models import Chunk, Document, Task
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.app.services.visual_asset_service import PdfVisualAssetService
from backend.app.orchestrators.document_ingestion import DocumentIngestionOrchestrator
from backend.infrastructure.database import create_database_engine, create_session_factory, initialize_database
from backend.infrastructure.llm import (
    create_embedding_client,
    create_vision_caption_client,
)
from backend.tests.support import build_test_settings, create_initialized_test_client, create_workspace_temp_dir


def _create_pdf_with_text_and_image(pdf_path: Path) -> None:
    image_path = pdf_path.parent / "phase3-sample.png"
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 24, 24), 0)
    pixmap.clear_with(0x00AAFF)
    pixmap.save(image_path)

    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "第一页：这是一份带图表的测试 PDF。")
    page.insert_image(fitz.Rect(72, 120, 220, 260), filename=str(image_path))
    document.save(pdf_path)
    document.close()


def _create_document_with_task(session_factory, storage_path: Path) -> tuple[str, str]:
    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="pdf",
            status="UPLOADED",
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.flush()

        task = Task(
            document_id=document.id,
            task_type="INGESTION",
            status="UPLOADED",
        )
        db_session.add(task)
        db_session.commit()
        return document.id, task.id


def test_phase3_acceptance_ingests_pdf_with_visual_chunks() -> None:
    temp_dir = create_workspace_temp_dir("phase3-acceptance")
    pdf_path = temp_dir / "visual-report.pdf"
    _create_pdf_with_text_and_image(pdf_path)

    settings = build_test_settings(
        temp_dir,
        overrides={
            "LLM_MODE": "acceptance",
            "MULTIMODAL_ENABLED": "true",
            "MAX_VISUAL_ASSETS_PER_DOCUMENT": "4",
        },
    )
    engine = create_database_engine(settings.database_url)
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = _create_document_with_task(session_factory, pdf_path)

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=DocumentParserService(),
        chunking_service=DocumentChunkingService(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        ),
        embedding_client=create_embedding_client(settings),
        visual_asset_service=PdfVisualAssetService(),
        vision_caption_client=create_vision_caption_client(settings),
        multimodal_enabled=settings.multimodal_enabled,
        max_visual_assets_per_document=settings.max_visual_assets_per_document,
    )

    result = orchestrator.process(document_id=document_id, task_id=task_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)
        chunks = db_session.query(Chunk).filter(Chunk.document_id == document_id).all()
        visual_chunks = [chunk for chunk in chunks if chunk.source_type != "text"]

    engine.dispose()

    assert result["status"] == "READY"
    assert document is not None and document.status == "READY"
    assert task is not None and task.status == "READY"
    assert visual_chunks
    assert visual_chunks[0].asset_label is not None
    assert visual_chunks[0].asset_path is not None


def test_phase3_acceptance_query_returns_visual_citations() -> None:
    temp_dir = create_workspace_temp_dir("phase3-query")
    pdf_path = temp_dir / "visual-report.pdf"
    _create_pdf_with_text_and_image(pdf_path)

    with create_initialized_test_client(
        overrides={
            "LLM_MODE": "acceptance",
            "MULTIMODAL_ENABLED": "true",
            "MAX_VISUAL_ASSETS_PER_DOCUMENT": "4",
        }
    ) as (client, _, settings):
        session_factory = client.app.state.db_session_factory
        document_id, task_id = _create_document_with_task(session_factory, pdf_path)

        orchestrator = DocumentIngestionOrchestrator(
            session_factory=session_factory,
            parser_service=DocumentParserService(),
            chunking_service=DocumentChunkingService(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            ),
            embedding_client=create_embedding_client(settings),
            visual_asset_service=PdfVisualAssetService(),
            vision_caption_client=create_vision_caption_client(settings),
            multimodal_enabled=settings.multimodal_enabled,
            max_visual_assets_per_document=settings.max_visual_assets_per_document,
        )
        result = orchestrator.process(document_id=document_id, task_id=task_id)
        assert result["status"] == "READY"

        detail_response = client.get(f"/api/documents/{document_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()
        assert detail_payload["data"]["has_visual_assets"] is True
        assert detail_payload["data"]["visual_asset_count"] >= 1

        response = client.post("/api/chat/sessions")
        session_id = response.json()["data"]["session_id"]

        query_response = client.post(
            "/api/chat/query",
            json={"session_id": session_id, "query": "第 1 页图表表达了什么"},
        )

        stream_response = client.post(
            "/api/chat/stream",
            json={"session_id": session_id, "query": "第 1 页图表表达了什么"},
        )

    assert query_response.status_code == 200
    payload = query_response.json()
    assert payload["success"] is True
    assert payload["data"]["citations"]
    assert any(citation["source_type"] != "text" for citation in payload["data"]["citations"])
    assert payload["data"]["answer"].startswith("【验收模式】")

    assert stream_response.status_code == 200
    body = stream_response.text
    assert '"source_type": "image"' in body or '"source_type": "page_snapshot"' in body
    assert "event: message_end" in body
