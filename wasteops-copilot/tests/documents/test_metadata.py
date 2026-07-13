"""Sidecar metadata validation tests."""

from pathlib import Path

import pytest

from app.ingestion.document_metadata import DocumentMetadataError, load_document_metadata


def test_valid_sidecar_and_unknown_field_modes(tmp_path: Path) -> None:
    document = tmp_path / "manual.pdf"
    document.write_bytes(b"pdf")
    sidecar = tmp_path / "manual.metadata.json"
    sidecar.write_text('{"title":"دليل","effective_date":"2026-01-01","extra":"ignored"}', encoding="utf-8")
    metadata = load_document_metadata(document)
    assert metadata.title == "دليل"
    assert str(metadata.effective_date) == "2026-01-01"
    with pytest.raises(DocumentMetadataError, match="Unknown"):
        load_document_metadata(document, strict=True)


def test_malformed_sidecar_is_rejected(tmp_path: Path) -> None:
    document = tmp_path / "manual.md"
    document.write_text("text", encoding="utf-8")
    (tmp_path / "manual.metadata.json").write_text("{bad", encoding="utf-8")
    with pytest.raises(DocumentMetadataError, match="valid UTF-8 JSON"):
        load_document_metadata(document)
