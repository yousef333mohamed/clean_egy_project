"""Pydantic-validated JSON sidecar metadata."""

import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas.documents import DocumentMetadata


class DocumentMetadataError(ValueError):
    """A metadata sidecar is malformed or violates its schema."""


def load_document_metadata(path: Path, *, strict: bool = False) -> DocumentMetadata:
    """Load ``name.metadata.json`` when present."""
    sidecar = path.with_suffix(".metadata.json")
    if not sidecar.exists():
        return DocumentMetadata()
    try:
        if sidecar.resolve(strict=True).parent != path.parent.resolve(strict=True):
            raise DocumentMetadataError("Metadata sidecar must remain beside its document")
        if sidecar.stat().st_size > 1024 * 1024:
            raise DocumentMetadataError("Metadata sidecar exceeds the 1 MB safety limit")
    except OSError as exc:
        raise DocumentMetadataError("Metadata sidecar is unavailable") from exc
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DocumentMetadataError("Metadata sidecar is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise DocumentMetadataError("Metadata sidecar must contain a JSON object")
    unknown = sorted(set(payload) - set(DocumentMetadata.model_fields))
    if strict and unknown:
        raise DocumentMetadataError(f"Unknown metadata fields: {', '.join(unknown)}")
    try:
        return DocumentMetadata.model_validate(payload)
    except ValidationError as exc:
        raise DocumentMetadataError("Metadata sidecar failed validation") from exc


def merge_metadata(base: DocumentMetadata, override: DocumentMetadata | None) -> DocumentMetadata:
    """Apply explicitly provided non-null metadata over a sidecar."""
    values = base.model_dump()
    if override is not None:
        values.update(override.model_dump(exclude_none=True))
    return DocumentMetadata.model_validate(values)
