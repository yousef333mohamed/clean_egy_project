"""Token-based deterministic chunking tests."""

from app.ingestion.document_chunker import DocumentChunker
from app.ingestion.document_loader import ExtractedBlock
from app.utils.token_counter import TokenCounter


def test_token_count_chunk_bounds_overlap_hashes_and_determinism() -> None:
    counter = TokenCounter("text-embedding-3-small")
    chunker = DocumentChunker(counter, chunk_size=30, overlap=5, minimum=5)
    text = " ".join(f"identifier-{index}" for index in range(80))
    blocks = [ExtractedBlock(text, page_number=1, section_title="Procedure")]
    first = chunker.chunk(blocks)
    second = chunker.chunk(blocks)
    assert first == second
    assert len(first) > 1
    assert all(0 < chunk.token_count <= 30 for chunk in first)
    assert all(len(chunk.content_hash) == 64 for chunk in first)
    prior = counter.encode(first[0].content)
    following = counter.encode(first[1].content)
    assert prior[-5:] == following[:5]


def test_small_adjacent_blocks_are_merged() -> None:
    counter = TokenCounter("text-embedding-3-small")
    chunker = DocumentChunker(counter, chunk_size=50, overlap=5, minimum=10)
    chunks = chunker.chunk([ExtractedBlock("Purpose"), ExtractedBlock("Check BIN-01 carefully.")])
    assert len(chunks) == 1
    assert "Purpose" in chunks[0].content
    assert "BIN-01" in chunks[0].content
