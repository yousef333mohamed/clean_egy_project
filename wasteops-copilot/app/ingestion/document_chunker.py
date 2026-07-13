"""Deterministic, structure-aware, token-based document chunking."""

from dataclasses import dataclass

from app.ingestion.document_loader import ExtractedBlock
from app.ingestion.text_cleaner import clean_text
from app.utils.document_hash import hash_content
from app.utils.token_counter import TokenCounter


@dataclass(frozen=True, slots=True)
class PreparedChunk:
    """A normalized chunk ready for embedding and storage."""

    chunk_number: int
    content: str
    content_hash: str
    token_count: int
    page_number: int | None
    section_title: str | None


class DocumentChunker:
    """Prefer source blocks and paragraphs before token-window fallback."""

    def __init__(self, counter: TokenCounter, *, chunk_size: int, overlap: int, minimum: int) -> None:
        if chunk_size <= 0 or minimum <= 0 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("invalid chunking configuration")
        self.counter = counter
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.minimum = minimum

    def _split_block(self, block: ExtractedBlock) -> list[tuple[str, int | None, str | None]]:
        cleaned = clean_text(block.text)
        if not cleaned:
            return []
        tokens = self.counter.encode(cleaned)
        if len(tokens) <= self.chunk_size:
            return [(cleaned, block.page_number, block.section_title)]
        step = self.chunk_size - self.overlap
        pieces = []
        for start in range(0, len(tokens), step):
            piece = clean_text(self.counter.decode(tokens[start : start + self.chunk_size]))
            if piece:
                pieces.append((piece, block.page_number, block.section_title))
            if start + self.chunk_size >= len(tokens):
                break
        return pieces

    def chunk(self, blocks: list[ExtractedBlock]) -> list[PreparedChunk]:
        """Create stable chunks, merging small adjacent blocks when possible."""
        units = [unit for block in blocks for unit in self._split_block(block)]
        merged: list[tuple[str, int | None, str | None]] = []
        for content, page, section in units:
            count = self.counter.count(content)
            if merged:
                prior, prior_page, prior_section = merged[-1]
                combined = f"{prior}\n\n{content}"
                same_structure = prior_page == page and prior_section == section
                small_boundary = count < self.minimum or self.counter.count(prior) < self.minimum
                if (same_structure or small_boundary) and self.counter.count(combined) <= self.chunk_size:
                    merged[-1] = (combined, prior_page if prior_page == page else None, prior_section or section)
                    continue
            merged.append((content, page, section))
        if len(merged) > 1 and self.counter.count(merged[-1][0]) < self.minimum:
            content, page, section = merged.pop()
            prior, prior_page, prior_section = merged[-1]
            combined = f"{prior}\n\n{content}"
            if self.counter.count(combined) <= self.chunk_size:
                merged[-1] = (combined, prior_page if prior_page == page else None, prior_section or section)
            else:
                merged.append((content, page, section))
        return [
            PreparedChunk(index, content, hash_content(content), self.counter.count(content), page, section)
            for index, (content, page, section) in enumerate(merged)
            if content.strip()
        ]
