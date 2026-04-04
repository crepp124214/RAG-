from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.exceptions import AppError
from backend.infrastructure.storage.file_storage import persist_upload_file, validate_upload_file
from backend.tests.support import create_workspace_temp_dir


def test_persist_upload_file_is_idempotent_for_same_content(monkeypatch: pytest.MonkeyPatch) -> None:
    storage_root = create_workspace_temp_dir("storage") / "uploads"
    content = b"phase-one document"

    first = persist_upload_file(storage_root, "demo.txt", content, max_upload_size_mb=2)

    def fail_if_rewritten(_: Path, __: bytes) -> int:
        raise AssertionError("existing file should not be rewritten")

    monkeypatch.setattr(Path, "write_bytes", fail_if_rewritten)

    second = persist_upload_file(storage_root, "demo.txt", content, max_upload_size_mb=2)

    assert first.storage_path == second.storage_path
    assert first.content_hash == second.content_hash
    assert first.storage_path.exists()
    assert first.storage_path.read_bytes() == content


@pytest.mark.parametrize(
    ("filename", "content", "max_upload_size_mb", "code"),
    [
        ("", b"hello", 2, "invalid_filename"),
        ("demo.txt", b"", 2, "empty_file"),
        ("demo.exe", b"hello", 2, "unsupported_file_type"),
        ("demo.txt", b"x" * (1024 * 1024 + 1), 1, "file_too_large"),
    ],
    ids=["blank-name", "empty-content", "unsupported-type", "too-large"],
)
def test_validate_upload_file_rejects_invalid_input(
    filename: str,
    content: bytes,
    max_upload_size_mb: int,
    code: str,
) -> None:
    with pytest.raises(AppError) as exc_info:
        validate_upload_file(filename, content, max_upload_size_mb)

    assert exc_info.value.code == code
