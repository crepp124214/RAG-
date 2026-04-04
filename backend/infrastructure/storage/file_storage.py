from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from backend.app.exceptions import AppError


ALLOWED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
}


@dataclass(frozen=True)
class StoredFile:
    original_name: str
    file_type: str
    storage_path: Path
    content_hash: str
    size_bytes: int


def validate_upload_file(filename: str | None, content: bytes, max_upload_size_mb: int) -> tuple[str, str]:
    resolved_name = (filename or "").strip()
    if not resolved_name:
        raise AppError("上传文件必须包含文件名", code="invalid_filename", status_code=400)
    if not content:
        raise AppError("上传文件不能为空", code="empty_file", status_code=400)

    size_limit_bytes = max_upload_size_mb * 1024 * 1024
    if len(content) > size_limit_bytes:
        raise AppError("上传文件超过大小限制", code="file_too_large", status_code=400)

    extension = Path(resolved_name).suffix.lower()
    file_type = ALLOWED_EXTENSIONS.get(extension)
    if file_type is None:
        raise AppError("不支持的文件类型", code="unsupported_file_type", status_code=400)

    return resolved_name, file_type


def build_storage_path(storage_root: Path, filename: str, content: bytes) -> tuple[Path, str]:
    content_hash = sha256(content).hexdigest()
    extension = Path(filename).suffix.lower()
    return storage_root / f"{content_hash}{extension}", content_hash


def persist_upload_file(storage_root: Path, filename: str | None, content: bytes, max_upload_size_mb: int) -> StoredFile:
    resolved_name, file_type = validate_upload_file(filename, content, max_upload_size_mb)
    storage_root.mkdir(parents=True, exist_ok=True)
    storage_path, content_hash = build_storage_path(storage_root, resolved_name, content)

    if not storage_path.exists():
        storage_path.write_bytes(content)

    return StoredFile(
        original_name=resolved_name,
        file_type=file_type,
        storage_path=storage_path,
        content_hash=content_hash,
        size_bytes=len(content),
    )
