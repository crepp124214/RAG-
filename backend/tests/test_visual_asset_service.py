from __future__ import annotations

import fitz

from backend.app.services.visual_asset_service import PdfVisualAssetService
from backend.tests.support import create_workspace_temp_dir


def test_extract_assets_returns_empty_for_text_only_pdf() -> None:
    temp_dir = create_workspace_temp_dir("visual-assets")
    pdf_path = temp_dir / "text-only.pdf"

    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "这是一页纯文本内容。")
    document.save(pdf_path)
    document.close()

    assets = PdfVisualAssetService().extract_assets(pdf_path, max_assets=5)

    assert assets == []


def test_extract_assets_extracts_embedded_images_from_pdf() -> None:
    temp_dir = create_workspace_temp_dir("visual-assets")
    pdf_path = temp_dir / "with-image.pdf"
    image_path = temp_dir / "sample.png"

    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 16, 16), 0)
    pixmap.clear_with(0xFF0000)
    pixmap.save(image_path)

    document = fitz.open()
    page = document.new_page()
    page.insert_image(fitz.Rect(72, 72, 180, 180), filename=str(image_path))
    document.save(pdf_path)
    document.close()

    assets = PdfVisualAssetService().extract_assets(pdf_path, max_assets=5)

    assert len(assets) == 1
    assert assets[0].page_number == 1
    assert assets[0].source_type == "image"


def test_extract_assets_falls_back_to_page_snapshot_for_scan_like_pdf() -> None:
    temp_dir = create_workspace_temp_dir("visual-assets")
    pdf_path = temp_dir / "scan-like.pdf"

    document = fitz.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    assets = PdfVisualAssetService().extract_assets(pdf_path, max_assets=5)

    assert len(assets) == 1
    assert assets[0].source_type == "page_snapshot"
    assert assets[0].page_number == 1
