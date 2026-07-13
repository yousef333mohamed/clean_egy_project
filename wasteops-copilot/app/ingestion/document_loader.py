"""Transparent text extraction for PDF, DOCX, Markdown, and UTF-8 text."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader


class DocumentLoadError(ValueError):
    """A source cannot be safely converted to extractable text."""


@dataclass(frozen=True, slots=True)
class ExtractedBlock:
    """A text block retaining source structure."""

    text: str
    page_number: int | None = None
    section_title: str | None = None
    kind: str = "paragraph"


@dataclass(slots=True)
class LoadedDocument:
    """Extracted blocks, page count, warnings, and basic source metadata."""

    blocks: list[ExtractedBlock]
    total_pages: int = 0
    warnings: list[str] = field(default_factory=list)
    source_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        return "\n\n".join(block.text for block in self.blocks if block.text.strip())


def load_pdf(path: Path) -> LoadedDocument:
    """Extract page text while preserving page boundaries."""
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise DocumentLoadError("PDF could not be opened") from exc
    if reader.is_encrypted:
        raise DocumentLoadError("Encrypted PDFs are not supported")
    blocks: list[ExtractedBlock] = []
    warnings: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise DocumentLoadError(f"PDF page {page_number} could not be extracted") from exc
        if text.strip():
            blocks.append(ExtractedBlock(text=text, page_number=page_number, kind="page"))
        else:
            warnings.append(f"Page {page_number} contained no extractable text.")
    if not blocks:
        raise DocumentLoadError("PDF contains no extractable text; OCR may be required")
    metadata = {str(key).lstrip("/"): str(value) for key, value in (reader.metadata or {}).items() if value is not None}
    return LoadedDocument(blocks, len(reader.pages), warnings, metadata)


def load_docx(path: Path) -> LoadedDocument:
    """Extract headings, paragraphs, and tables from a DOCX document."""
    try:
        document = Document(path)
    except Exception as exc:
        raise DocumentLoadError("DOCX could not be opened") from exc
    blocks: list[ExtractedBlock] = []
    section: str | None = None
    for item in document.iter_inner_content():
        if isinstance(item, Paragraph):
            text = item.text.strip()
            if not text:
                continue
            style = item.style.name if item.style is not None else ""
            if style.lower().startswith("heading"):
                section = text
                blocks.append(ExtractedBlock(text=f"# {text}", section_title=section, kind="heading"))
            else:
                blocks.append(ExtractedBlock(text=text, section_title=section))
        elif isinstance(item, Table):
            rows = [" | ".join(cell.text.strip().replace("\n", " ") for cell in row.cells) for row in item.rows]
            rendered = "\n".join(row for row in rows if row.strip(" |"))
            if rendered:
                blocks.append(ExtractedBlock(text=rendered, section_title=section, kind="table"))
    if not blocks:
        raise DocumentLoadError("DOCX contains no extractable text")
    properties = document.core_properties
    metadata = {key: value for key in ("title", "subject", "author") if (value := getattr(properties, key, None))}
    return LoadedDocument(blocks, source_metadata=metadata)


def load_markdown(path: Path) -> LoadedDocument:
    """Preserve Markdown headings, lists, paragraphs, and code fences."""
    text = _read_utf8(path)
    if not text.strip():
        raise DocumentLoadError("Markdown document is empty")
    blocks: list[ExtractedBlock] = []
    section: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            content = "\n".join(buffer).strip()
            if content:
                blocks.append(ExtractedBlock(content, section_title=section))
            buffer.clear()

    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            buffer.append(line)
            continue
        match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", line)
        if match and not in_code:
            flush()
            section = match.group(2).strip()
            blocks.append(ExtractedBlock(line.strip(), section_title=section, kind="heading"))
        elif not line.strip() and not in_code:
            flush()
        else:
            buffer.append(line.rstrip())
    flush()
    return LoadedDocument(blocks)


def load_text(path: Path) -> LoadedDocument:
    """Read UTF-8 or UTF-8-with-BOM text without guessing encodings."""
    text = _read_utf8(path)
    if not text.strip():
        raise DocumentLoadError("Text document is empty")
    blocks = [ExtractedBlock(paragraph) for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    return LoadedDocument(blocks)


def _read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentLoadError("Text must be encoded as UTF-8 or UTF-8 with BOM") from exc


def load_document(path: Path) -> LoadedDocument:
    """Dispatch by the previously allow-listed extension."""
    extension = path.suffix.lower()
    if extension == ".pdf":
        return load_pdf(path)
    if extension == ".docx":
        return load_docx(path)
    if extension == ".md":
        return load_markdown(path)
    if extension == ".txt":
        return load_text(path)
    raise DocumentLoadError(f"Unsupported document extension: {extension}")
