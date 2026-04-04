from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document

from backend.app.exceptions import AppError


class DocumentParserService:
    def parse_file(self, storage_path: str | Path, *, file_type: str, original_name: str) -> list[Document]:
        file_path = Path(storage_path).resolve()
        if not file_path.exists():
            raise AppError("待解析文件不存在", code="document_file_not_found", status_code=404)

        loader = self._build_loader(file_path, file_type)
        try:
            documents = loader.load()
        except Exception as exc:  # pragma: no cover - exercised through tests via monkeypatch
            raise AppError("文档解析失败", code="document_parse_failed", status_code=400) from exc

        return [self._normalize_document(doc, file_path, file_type, original_name) for doc in documents]

    def _build_loader(self, file_path: Path, file_type: str):
        if file_type == "pdf":
            return PyPDFLoader(str(file_path))
        if file_type == "docx":
            return Docx2txtLoader(str(file_path))
        if file_type == "txt":
            return TextLoader(str(file_path), encoding="utf-8")
        raise AppError("不支持的解析文件类型", code="unsupported_file_type", status_code=400)

    def _normalize_document(
        self,
        document: Document,
        file_path: Path,
        file_type: str,
        original_name: str,
    ) -> Document:
        metadata = dict(document.metadata)
        metadata["source"] = original_name
        metadata["file_type"] = file_type
        metadata["storage_path"] = str(file_path)

        raw_page = metadata.get("page")
        if isinstance(raw_page, int):
            metadata["page_number"] = raw_page + 1
        elif "page_number" not in metadata:
            metadata["page_number"] = None

        return Document(page_content=document.page_content, metadata=metadata)
