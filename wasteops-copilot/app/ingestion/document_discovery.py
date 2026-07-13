"""Recursive, allow-listed knowledge-document discovery."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".docx", ".txt", ".md"})
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class DocumentPathError(ValueError):
    """A requested path is unsafe or not an ingestible document."""


@dataclass(frozen=True, slots=True)
class DiscoveredDocument:
    """Safe public metadata for a discovered file."""

    filename: str
    relative_path: str
    extension: str
    size_bytes: int
    modified_at: datetime
    supported: bool
    rejection_reason: str | None = None
    path: Path | None = None


def _ignored(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return (
        any(part.startswith(".") for part in relative.parts)
        or path.name.startswith("~$")
        or path.suffix.lower() in {".tmp", ".part"}
        or path.name.endswith(".metadata.json")
    )


def discover_documents(documents_dir: Path, max_file_size_mb: int) -> list[DiscoveredDocument]:
    """Discover documents recursively without following escapes or temp files."""
    root = documents_dir.resolve()
    if not root.exists():
        return []
    maximum = max_file_size_mb * 1024 * 1024
    results: list[DiscoveredDocument] = []
    for candidate in sorted((item for item in root.rglob("*") if item.is_file() or item.is_symlink()), key=lambda item: item.as_posix().lower()):
        if _ignored(candidate, root):
            continue
        relative = candidate.relative_to(root).as_posix()
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            results.append(
                DiscoveredDocument(
                    candidate.name,
                    relative,
                    candidate.suffix.lower(),
                    0,
                    datetime.now(UTC),
                    False,
                    "file or symbolic-link target is unavailable",
                )
            )
            continue
        try:
            resolved.relative_to(root)
        except ValueError:
            results.append(
                DiscoveredDocument(candidate.name, relative, candidate.suffix.lower(), 0, datetime.now(UTC), False, "symbolic link escapes document directory")
            )
            continue
        size = resolved.stat().st_size
        extension = candidate.suffix.lower()
        reason = None
        supported = extension in SUPPORTED_EXTENSIONS
        if not supported:
            reason = "unsupported file extension"
        elif size > maximum:
            supported = False
            reason = f"file exceeds {max_file_size_mb} MB limit"
        stat = resolved.stat()
        results.append(
            DiscoveredDocument(
                candidate.name,
                relative,
                extension,
                size,
                datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                supported,
                reason,
                resolved if supported else None,
            )
        )
    return results


def resolve_document(documents_dir: Path, relative_path: str, max_file_size_mb: int) -> DiscoveredDocument:
    """Resolve a client-supplied relative path only through discovered files."""
    pure = PurePosixPath(relative_path)
    if not relative_path or "\\" in relative_path or pure.is_absolute() or ".." in pure.parts:
        raise DocumentPathError("relative_path must be a safe relative POSIX path")
    normalized = pure.as_posix()
    for item in discover_documents(documents_dir, max_file_size_mb):
        if item.relative_path == normalized:
            if not item.supported:
                raise DocumentPathError(item.rejection_reason or "document is not supported")
            return item
    raise DocumentPathError("document was not found")
