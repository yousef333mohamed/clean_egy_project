"""Explainable deterministic reranking and diversity tests."""

import pytest

from app.retrieval.reranker import EvidenceReranker
from app.utils.text_similarity import limit_document_chunks


@pytest.mark.asyncio
async def test_coverage_identifier_score_bounds_and_determinism(evidence_factory) -> None:
    exact = evidence_factory(chunk_id="1", content="Inspect BIN-DEMO-001 sensor fault", final_score=0.7)
    unrelated = evidence_factory(chunk_id="2", document_id="doc-2", content="Workforce leave schedule", final_score=0.7)
    reranker = EvidenceReranker()
    first = await reranker.rerank("BIN-DEMO-001 sensor fault", [unrelated, exact], top_k=2)
    second = await reranker.rerank("BIN-DEMO-001 sensor fault", [unrelated, exact], top_k=2)
    assert first == second
    assert first[0].chunk_id == "1"
    assert all(0 <= item.rerank_score <= 1 and 0 <= item.final_score <= 1 for item in first)


def test_document_limit_and_content_hash_deduplication(evidence_factory) -> None:
    items = [
        evidence_factory(chunk_id="1", content_hash="same"),
        evidence_factory(chunk_id="2", content_hash="same"),
        evidence_factory(chunk_id="3", content_hash="other"),
    ]
    selected = limit_document_chunks(items, 1)
    assert [item.chunk_id for item in selected] == ["1"]
