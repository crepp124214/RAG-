from __future__ import annotations

from pathlib import Path

import pytest
from langchain_core.documents import Document as LangChainDocument
from sqlalchemy import select

from backend.app.models import Chunk, Document, Task
from backend.app.orchestrators.document_ingestion import DocumentIngestionOrchestrator
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.infrastructure.database import create_database_engine, create_session_factory, initialize_database
from backend.tests.support import create_workspace_temp_dir


class FakeEmbeddingClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.fail:
            raise RuntimeError("embedding unavailable")
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeVisualAssetService:
    def __init__(self, assets: list[object] | None = None) -> None:
        self.assets = assets or []

    def extract_assets(self, storage_path: str | Path, *, max_assets: int) -> list[object]:
        del storage_path, max_assets
        return self.assets


class FakeVisionCaptionClient:
    def __init__(self, *, fail_asset_indexes: set[int] | None = None) -> None:
        self.fail_asset_indexes = fail_asset_indexes or set()

    def describe_image(self, *, image_path: str, asset_label: str) -> str:
        del image_path
        if any(str(index) in asset_label for index in self.fail_asset_indexes):
            raise RuntimeError("vision unavailable")
        return f"{asset_label} 的视觉描述"


def create_document_with_task(session_factory, storage_path: Path) -> tuple[str, str]:
    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="txt",
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


def test_document_ingestion_processes_document_to_ready() -> None:
    temp_dir = create_workspace_temp_dir("ingestion")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("第一段。\n第二段。\n第三段。", encoding="utf-8")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'ingestion.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = create_document_with_task(session_factory, storage_path)

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=DocumentParserService(),
        chunking_service=DocumentChunkingService(chunk_size=12, chunk_overlap=2),
        embedding_client=FakeEmbeddingClient(),
    )

    result = orchestrator.process(document_id=document_id, task_id=task_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)
        chunks = db_session.scalars(select(Chunk).order_by(Chunk.chunk_index)).all()

    engine.dispose()

    assert result["status"] == "READY"
    assert document is not None and document.status == "READY"
    assert task is not None and task.status == "READY"
    assert task.error_message is None
    assert len(chunks) >= 1
    assert all(chunk.embedding is not None for chunk in chunks)


def test_document_ingestion_marks_document_and_task_failed_on_error() -> None:
    temp_dir = create_workspace_temp_dir("ingestion")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("第一段。\n第二段。", encoding="utf-8")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'failure.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)
    document_id, task_id = create_document_with_task(session_factory, storage_path)

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=DocumentParserService(),
        chunking_service=DocumentChunkingService(chunk_size=12, chunk_overlap=2),
        embedding_client=FakeEmbeddingClient(fail=True),
    )

    with pytest.raises(RuntimeError):
        orchestrator.process(document_id=document_id, task_id=task_id)

    with session_factory() as db_session:
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)

    engine.dispose()

    assert document is not None and document.status == "FAILED"
    assert task is not None and task.status == "FAILED"
    assert task.error_message == "embedding unavailable"


def test_document_ingestion_persists_visual_chunks_when_pdf_assets_exist() -> None:
    temp_dir = create_workspace_temp_dir("ingestion-visual")
    storage_path = temp_dir / "demo.pdf"
    storage_path.write_bytes(b"%PDF-1.4 minimal")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'visual.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="pdf",
            status="UPLOADED",
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.flush()
        task = Task(document_id=document.id, task_type="INGESTION", status="UPLOADED")
        db_session.add(task)
        db_session.commit()
        document_id, task_id = document.id, task.id

    visual_assets = [
        type(
            "Asset",
            (),
            {
                "page_number": 1,
                "asset_index": 0,
                "asset_label": "第 1 页图片 0",
                "asset_path": str(temp_dir / "image-0.png"),
                "bbox": None,
                "source_type": "image",
            },
        )()
    ]

    class FakeParserService:
        def parse_file(self, storage_path: str | Path, *, file_type: str, original_name: str) -> list[LangChainDocument]:
            del storage_path, file_type, original_name
            return [LangChainDocument(page_content="文本文档内容", metadata={"page_number": 1})]

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=FakeParserService(),
        chunking_service=DocumentChunkingService(chunk_size=200, chunk_overlap=20),
        embedding_client=FakeEmbeddingClient(),
        visual_asset_service=FakeVisualAssetService(visual_assets),
        vision_caption_client=FakeVisionCaptionClient(),
        multimodal_enabled=True,
        max_visual_assets_per_document=4,
    )

    result = orchestrator.process(document_id=document_id, task_id=task_id)

    with session_factory() as db_session:
        chunks = db_session.scalars(select(Chunk).order_by(Chunk.chunk_index)).all()
        visual_chunks = [chunk for chunk in chunks if chunk.source_type == "image"]
        document = db_session.get(Document, document_id)
        task = db_session.get(Task, task_id)

    engine.dispose()

    assert result["status"] == "READY"
    assert document is not None and document.status == "READY"
    assert task is not None and task.status == "READY"
    assert len(visual_chunks) == 1
    assert visual_chunks[0].asset_label == "第 1 页图片 0"
    assert visual_chunks[0].asset_index == 0


def test_document_ingestion_skips_failed_visual_caption_when_text_chunks_exist() -> None:
    temp_dir = create_workspace_temp_dir("ingestion-visual-skip")
    storage_path = temp_dir / "demo.pdf"
    storage_path.write_bytes(b"%PDF-1.4 minimal")

    engine = create_database_engine(f"sqlite+pysqlite:///{(temp_dir / 'visual-skip.sqlite3').resolve()}")
    initialize_database(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db_session:
        document = Document(
            name=storage_path.name,
            file_type="pdf",
            status="UPLOADED",
            storage_path=str(storage_path),
        )
        db_session.add(document)
        db_session.flush()
        task = Task(document_id=document.id, task_type="INGESTION", status="UPLOADED")
        db_session.add(task)
        db_session.commit()
        document_id, task_id = document.id, task.id

    visual_assets = [
        type(
            "Asset",
            (),
            {
                "page_number": 1,
                "asset_index": 1,
                "asset_label": "第 1 页图片 1",
                "asset_path": str(temp_dir / "image-1.png"),
                "bbox": None,
                "source_type": "image",
            },
        )()
    ]

    class FakeParserService:
        def parse_file(self, storage_path: str | Path, *, file_type: str, original_name: str) -> list[LangChainDocument]:
            del storage_path, file_type, original_name
            return [LangChainDocument(page_content="保底文本内容", metadata={"page_number": 1})]

    orchestrator = DocumentIngestionOrchestrator(
        session_factory=session_factory,
        parser_service=FakeParserService(),
        chunking_service=DocumentChunkingService(chunk_size=200, chunk_overlap=20),
        embedding_client=FakeEmbeddingClient(),
        visual_asset_service=FakeVisualAssetService(visual_assets),
        vision_caption_client=FakeVisionCaptionClient(fail_asset_indexes={1}),
        multimodal_enabled=True,
        max_visual_assets_per_document=4,
    )

    result = orchestrator.process(document_id=document_id, task_id=task_id)

    with session_factory() as db_session:
        chunks = db_session.scalars(select(Chunk).order_by(Chunk.chunk_index)).all()

    engine.dispose()

    assert result["status"] == "READY"
    assert any(chunk.source_type == "text" for chunk in chunks)
    assert all(chunk.source_type != "image" for chunk in chunks)
