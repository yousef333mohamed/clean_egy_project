"""Safe recursive document discovery tests."""

import os
from pathlib import Path

import pytest

from app.ingestion.document_discovery import DocumentPathError, discover_documents, resolve_document


def test_nested_supported_and_unsupported_files(tmp_path: Path) -> None:
    nested = tmp_path / "manuals"
    nested.mkdir()
    (nested / "sensor.md").write_text("# Sensor", encoding="utf-8")
    (nested / "archive.exe").write_bytes(b"x")
    (nested / ".hidden.md").write_text("hidden", encoding="utf-8")
    (nested / "~$draft.docx").write_bytes(b"temp")
    results = discover_documents(tmp_path, 1)
    assert [(item.relative_path, item.supported) for item in results] == [
        ("manuals/archive.exe", False),
        ("manuals/sensor.md", True),
    ]


def test_traversal_absolute_and_oversized_files_are_rejected(tmp_path: Path) -> None:
    large = tmp_path / "large.txt"
    large.write_bytes(b"x" * (1024 * 1024 + 1))
    assert discover_documents(tmp_path, 1)[0].supported is False
    for path in ("../secret.txt", str((tmp_path / "large.txt").resolve()), "folder\\file.txt"):
        with pytest.raises(DocumentPathError):
            resolve_document(tmp_path, path, 1)


def test_symbolic_link_escape_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.md"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "escape.md"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("symbolic links are unavailable")
    try:
        item = next(item for item in discover_documents(tmp_path, 1) if item.relative_path == "escape.md")
        assert item.supported is False
        assert "escapes" in (item.rejection_reason or "")
    finally:
        outside.unlink(missing_ok=True)
