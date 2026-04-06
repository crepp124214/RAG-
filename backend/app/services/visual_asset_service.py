from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

from backend.app.exceptions import AppError


@dataclass(frozen=True)
class VisualAssetPayload:
    page_number: int
    asset_index: int
    asset_label: str
    asset_path: str
    bbox: dict[str, float] | None
    source_type: str


class PdfVisualAssetService:
    def extract_assets(
        self,
        storage_path: str | Path,
        *,
        max_assets: int,
    ) -> list[VisualAssetPayload]:
        file_path = Path(storage_path).resolve()
        if not file_path.exists():
            raise AppError("待提取视觉资产的文件不存在", code="document_file_not_found", status_code=404)
        if max_assets <= 0:
            return []

        asset_dir = self._build_asset_dir(file_path)
        asset_dir.mkdir(parents=True, exist_ok=True)

        assets: list[VisualAssetPayload] = []
        try:
            with fitz.open(file_path) as pdf_document:
                for page_index in range(pdf_document.page_count):
                    if len(assets) >= max_assets:
                        break

                    page = pdf_document.load_page(page_index)
                    page_number = page_index + 1
                    page_text = page.get_text("text").strip()
                    page_assets = self._extract_page_images(
                        pdf_document,
                        page,
                        page_number=page_number,
                        asset_dir=asset_dir,
                        start_index=len(assets),
                        remaining=max_assets - len(assets),
                    )
                    assets.extend(page_assets)

                    if len(assets) >= max_assets:
                        break

                    if not page_text and not page_assets:
                        snapshot = self._render_page_snapshot(
                            page,
                            page_number=page_number,
                            asset_dir=asset_dir,
                            asset_index=len(assets),
                        )
                        assets.append(snapshot)
        except AppError:
            raise
        except Exception as exc:  # pragma: no cover - exercised in tests via monkeypatch
            raise AppError("PDF 视觉资产提取失败", code="visual_asset_extract_failed", status_code=400) from exc

        return assets

    def _extract_page_images(
        self,
        pdf_document: fitz.Document,
        page: fitz.Page,
        *,
        page_number: int,
        asset_dir: Path,
        start_index: int,
        remaining: int,
    ) -> list[VisualAssetPayload]:
        assets: list[VisualAssetPayload] = []
        for image_offset, image_info in enumerate(page.get_images(full=True), start=1):
            if len(assets) >= remaining:
                break

            xref = image_info[0]
            pixmap = fitz.Pixmap(pdf_document, xref)
            try:
                if pixmap.alpha or pixmap.n > 4:
                    pixmap = fitz.Pixmap(fitz.csRGB, pixmap)

                asset_index = start_index + len(assets)
                asset_path = asset_dir / f"page-{page_number:03d}-image-{image_offset:02d}.png"
                pixmap.save(asset_path)
                assets.append(
                    VisualAssetPayload(
                        page_number=page_number,
                        asset_index=asset_index,
                        asset_label=f"第 {page_number} 页图片 {image_offset}",
                        asset_path=str(asset_path),
                        bbox=None,
                        source_type="image",
                    )
                )
            finally:
                pixmap = None

        return assets

    def _render_page_snapshot(
        self,
        page: fitz.Page,
        *,
        page_number: int,
        asset_dir: Path,
        asset_index: int,
    ) -> VisualAssetPayload:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        try:
            asset_path = asset_dir / f"page-{page_number:03d}-snapshot.png"
            pixmap.save(asset_path)
        finally:
            pixmap = None

        return VisualAssetPayload(
            page_number=page_number,
            asset_index=asset_index,
            asset_label=f"第 {page_number} 页整页图像",
            asset_path=str(asset_path),
            bbox=None,
            source_type="page_snapshot",
        )

    def _build_asset_dir(self, file_path: Path) -> Path:
        return file_path.parent / f"{file_path.stem}_assets"


def build_visual_caption_document(asset: VisualAssetPayload, caption: str) -> dict[str, Any]:
    return {
        "page_content": caption,
        "metadata": {
            "page_number": asset.page_number,
            "source_type": asset.source_type,
            "asset_index": asset.asset_index,
            "asset_label": asset.asset_label,
            "asset_path": asset.asset_path,
            "bbox": asset.bbox,
        },
    }
