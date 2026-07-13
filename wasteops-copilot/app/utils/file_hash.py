"""Streaming cryptographic file hashes."""

import hashlib
from pathlib import Path


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    """Calculate SHA-256 without loading the source file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(block_size), b""):
            digest.update(block)
    return digest.hexdigest()
