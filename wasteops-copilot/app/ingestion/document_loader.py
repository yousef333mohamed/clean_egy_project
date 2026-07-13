"""Document text extraction."""

from pathlib import Path
from docx import Document
from pypdf import PdfReader
from app.ingestion.chunker import clean_text
from app.utils.exceptions import IngestionError

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def extract_document(path: Path) -> str:
    """Extract clean text from PDF, text, Markdown, or DOCX."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise IngestionError(f"Unsupported document type: {suffix}")
    if suffix == ".pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    elif suffix == ".docx":
        text = "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    else:
        text = path.read_text(encoding="utf-8")
    text = clean_text(text)
    if not text:
        raise IngestionError("Document contains no extractable text")
    return text
