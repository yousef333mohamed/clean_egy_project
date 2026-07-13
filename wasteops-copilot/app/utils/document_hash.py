"""Document and chunk SHA-256 helpers."""

import hashlib
from pathlib import Path

from app.utils.file_hash import sha256_file


def hash_document(path: Path) -> str:
    """Hash a source document without loading it into memory."""
    return sha256_file(path)


def hash_content(content: str) -> str:
    """Hash normalized UTF-8 chunk content deterministically."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
