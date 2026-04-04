from __future__ import annotations

from pathlib import Path

import pytest
from langchain_core.documents import Document

from backend.app.exceptions import AppError
from backend.app.services.parser_service import DocumentParserService
from backend.tests.support import create_workspace_temp_dir


class FakeLoader:
    def __init__(self, documents: list[Document] | None = None, error: Exception | None = None) -> None:
        self.documents = documents or []
        self.error = error

    def load(self) -> list[Document]:
        if self.error is not None:
            raise self.error
        return self.documents


def test_parse_file_supports_txt_files() -> None:
    temp_dir = create_workspace_temp_dir("parser")
    storage_path = temp_dir / "demo.txt"
    storage_path.write_text("第一段\n第二段", encoding="utf-8")

    documents = DocumentParserService().parse_file(
        storage_path,
        file_type="txt",
        original_name="demo.txt",
    )

    assert len(documents) == 1
    assert documents[0].page_content == "第一段\n第二段"
    assert documents[0].metadata["source"] == "demo.txt"
    assert documents[0].metadata["file_type"] == "txt"
    assert documents[0].metadata["storage_path"] == str(storage_path.resolve())
    assert documents[0].metadata["page_number"] is None


def test_parse_file_uses_pdf_loader_and_normalizes_page_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = create_workspace_temp_dir("parser")
    storage_path = temp_dir / "report.pdf"
    storage_path.write_bytes(b"%PDF-1.4")

    def fake_pdf_loader(path: str) -> FakeLoader:
        assert path == str(storage_path.resolve())
        return FakeLoader([Document(page_content="pdf-content", metadata={"page": 0})])

    monkeypatch.setattr("backend.app.services.parser_service.PyPDFLoader", fake_pdf_loader)

    documents = DocumentParserService().parse_file(
        storage_path,
        file_type="pdf",
        original_name="report.pdf",
    )

    assert len(documents) == 1
    assert documents[0].metadata["page_number"] == 1
    assert documents[0].metadata["source"] == "report.pdf"


def test_parse_file_uses_docx_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = create_workspace_temp_dir("parser")
    storage_path = temp_dir / "notes.docx"
    storage_path.write_bytes(b"PK\x03\x04")

    def fake_docx_loader(path: str) -> FakeLoader:
        assert path == str(storage_path.resolve())
        return FakeLoader([Document(page_content="docx-content", metadata={})])

    monkeypatch.setattr("backend.app.services.parser_service.Docx2txtLoader", fake_docx_loader)

    documents = DocumentParserService().parse_file(
        storage_path,
        file_type="docx",
        original_name="notes.docx",
    )

    assert len(documents) == 1
    assert documents[0].page_content == "docx-content"
    assert documents[0].metadata["source"] == "notes.docx"


def test_parse_file_rejects_missing_file() -> None:
    with pytest.raises(AppError) as exc_info:
        DocumentParserService().parse_file(
            Path("backend/tests/.tmp/missing.txt"),
            file_type="txt",
            original_name="missing.txt",
        )

    assert exc_info.value.code == "document_file_not_found"


def test_parse_file_wraps_loader_error(monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = create_workspace_temp_dir("parser")
    storage_path = temp_dir / "broken.pdf"
    storage_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        "backend.app.services.parser_service.PyPDFLoader",
        lambda path: FakeLoader(error=ValueError("broken file")),
    )

    with pytest.raises(AppError) as exc_info:
        DocumentParserService().parse_file(
            storage_path,
            file_type="pdf",
            original_name="broken.pdf",
        )

    assert exc_info.value.code == "document_parse_failed"
