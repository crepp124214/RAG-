from __future__ import annotations

import logging

from langchain_core.documents import Document as LangChainDocument
from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from backend.app.exceptions import AppError
from backend.app.models import Chunk, Document, Task
from backend.app.services.chunking_service import DocumentChunkingService
from backend.app.services.parser_service import DocumentParserService
from backend.app.services.visual_asset_service import PdfVisualAssetService, build_visual_caption_document
from backend.infrastructure.observability import log_event
from backend.infrastructure.vector.store import ensure_vector_extension, update_chunk_embedding


logger = logging.getLogger(__name__)


class DocumentIngestionOrchestrator:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        parser_service: DocumentParserService,
        chunking_service: DocumentChunkingService,
        embedding_client: object,
        visual_asset_service: PdfVisualAssetService | None = None,
        vision_caption_client: object | None = None,
        multimodal_enabled: bool = False,
        max_visual_assets_per_document: int = 0,
    ) -> None:
        self.session_factory = session_factory
        self.parser_service = parser_service
        self.chunking_service = chunking_service
        self.embedding_client = embedding_client
        self.visual_asset_service = visual_asset_service
        self.vision_caption_client = vision_caption_client
        self.multimodal_enabled = multimodal_enabled
        self.max_visual_assets_per_document = max_visual_assets_per_document

    def process(self, *, document_id: str, task_id: str) -> dict[str, str | int]:
        with self.session_factory() as db_session:
            document = db_session.get(Document, document_id)
            task = db_session.get(Task, task_id)
            if document is None:
                raise AppError("文档不存在", code="document_not_found", status_code=404)
            if task is None:
                raise AppError("任务不存在", code="task_not_found", status_code=404)

            log_event(
                logger,
                logging.INFO,
                "document.ingestion_started",
                document_id=document.id,
                task_id=task.id,
            )

            try:
                self._set_status(db_session, document=document, task=task, status="PARSING")
                parsed_documents = self.parser_service.parse_file(
                    document.storage_path,
                    file_type=document.file_type,
                    original_name=document.name,
                )
                if not parsed_documents:
                    raise AppError("文档解析结果为空", code="document_parse_empty", status_code=400)

                visual_documents = self._build_visual_documents(db_session, document=document, task=task)
                if not parsed_documents and not visual_documents:
                    raise AppError("文档解析结果为空", code="document_parse_empty", status_code=400)

                self._set_status(db_session, document=document, task=task, status="CHUNKING")
                text_chunk_payloads = self.chunking_service.split_documents(
                    parsed_documents,
                    document_id=document.id,
                    source_type="text",
                )
                visual_chunk_payloads = self.chunking_service.split_documents(
                    visual_documents,
                    document_id=document.id,
                    source_type="visual",
                    preserve_documents=True,
                )
                chunk_payloads = [*text_chunk_payloads, *visual_chunk_payloads]
                if not chunk_payloads:
                    raise AppError("文档分块结果为空", code="document_chunk_empty", status_code=400)

                self._set_status(db_session, document=document, task=task, status="EMBEDDING")
                embeddings = self.embedding_client.embed_texts(
                    [payload.content for payload in chunk_payloads]
                )
                if len(embeddings) != len(chunk_payloads):
                    raise AppError("向量化结果数量不匹配", code="embedding_result_mismatch", status_code=502)

                self._replace_chunks(
                    db_session,
                    document=document,
                    chunk_payloads=chunk_payloads,
                    embeddings=embeddings,
                )

                document.status = "READY"
                task.status = "READY"
                task.error_message = None
                db_session.add_all([document, task])
                db_session.commit()

                log_event(
                    logger,
                    logging.INFO,
                    "document.ingestion_completed",
                    document_id=document.id,
                    task_id=task.id,
                    chunk_count=len(chunk_payloads),
                )

                return {
                    "document_id": document.id,
                    "task_id": task.id,
                    "status": "READY",
                    "chunk_count": len(chunk_payloads),
                }
            except Exception as exc:
                db_session.rollback()
                self._mark_failed(db_session, document=document, task=task, error_message=str(exc))
                log_event(
                    logger,
                    logging.ERROR,
                    "document.ingestion_failed",
                    document_id=document.id,
                    task_id=task.id,
                    error_message=str(exc),
                )
                raise

    def _replace_chunks(
        self,
        db_session: Session,
        *,
        document: Document,
        chunk_payloads: list,
        embeddings: list[list[float]],
    ) -> None:
        ensure_vector_extension(db_session)
        db_session.execute(delete(Chunk).where(Chunk.document_id == document.id))
        db_session.flush()

        for payload, embedding in zip(chunk_payloads, embeddings, strict=True):
            chunk = Chunk(
                document_id=document.id,
                chunk_index=payload.chunk_index,
                content=payload.content,
                source_type=payload.source_type,
                page_number=payload.page_number,
                asset_index=self._as_int(payload.metadata.get("asset_index")),
                asset_label=self._as_str(payload.metadata.get("asset_label")),
                asset_path=self._as_str(payload.metadata.get("asset_path")),
                bbox=self._as_bbox(payload.metadata.get("bbox")),
            )
            db_session.add(chunk)
            db_session.flush()
            update_chunk_embedding(db_session, chunk.id, embedding)

        db_session.commit()

    def _set_status(
        self,
        db_session: Session,
        *,
        document: Document,
        task: Task,
        status: str,
    ) -> None:
        document.status = status
        task.status = status
        task.error_message = None
        db_session.add_all([document, task])
        db_session.commit()
        log_event(
            logger,
            logging.INFO,
            "document.status_changed",
            document_id=document.id,
            task_id=task.id,
            status=status,
        )

    def _mark_failed(
        self,
        db_session: Session,
        *,
        document: Document,
        task: Task,
        error_message: str,
    ) -> None:
        document.status = "FAILED"
        task.status = "FAILED"
        task.error_message = error_message[:2000]
        db_session.add_all([document, task])
        db_session.commit()

    def _build_visual_documents(
        self,
        db_session: Session,
        *,
        document: Document,
        task: Task,
    ) -> list[LangChainDocument]:
        if (
            document.file_type != "pdf"
            or not self.multimodal_enabled
            or self.visual_asset_service is None
            or self.vision_caption_client is None
            or self.max_visual_assets_per_document <= 0
        ):
            return []

        self._set_status(db_session, document=document, task=task, status="VISUAL_EXTRACTING")
        assets = self.visual_asset_service.extract_assets(
            document.storage_path,
            max_assets=self.max_visual_assets_per_document,
        )
        visual_documents: list[LangChainDocument] = []
        for asset in assets:
            try:
                caption = self.vision_caption_client.describe_image(
                    image_path=asset.asset_path,
                    asset_label=asset.asset_label,
                )
            except Exception as exc:  # pragma: no cover - exercised in tests via fake client
                log_event(
                    logger,
                    logging.WARNING,
                    "document.visual_caption_failed",
                    document_id=document.id,
                    task_id=task.id,
                    page_number=asset.page_number,
                    asset_index=asset.asset_index,
                    source_type=asset.source_type,
                    error_message=str(exc),
                )
                continue

            payload = build_visual_caption_document(asset, caption)
            visual_documents.append(
                LangChainDocument(
                    page_content=str(payload["page_content"]),
                    metadata=dict(payload["metadata"]),
                )
            )

        return visual_documents

    def _as_str(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _as_int(self, value: object) -> int | None:
        return value if isinstance(value, int) else None

    def _as_bbox(self, value: object) -> dict[str, float] | None:
        if not isinstance(value, dict):
            return None
        normalized: dict[str, float] = {}
        for key, item in value.items():
            if isinstance(item, (int, float)):
                normalized[str(key)] = float(item)
        return normalized or None
