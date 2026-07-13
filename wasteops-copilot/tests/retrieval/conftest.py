"""Shared retrieval evidence fixtures."""

from datetime import date

import pytest

from app.schemas.retrieval import RetrievedEvidence


@pytest.fixture
def evidence_factory():
    def factory(**overrides):
        values = {
            "chunk_id": "1",
            "document_id": "doc-1",
            "source_filename": "smart_bin_sensor_fault_sop.md",
            "document_title": "Synthetic Smart-Bin Sensor Fault SOP",
            "document_type": "operational_sop",
            "department": "operations",
            "asset_type": "smart_bin",
            "region": "Greater Cairo",
            "language": "en",
            "version": "1.0",
            "effective_date": date(2026, 1, 1),
            "authority_level": "demo_only",
            "page_number": None,
            "section_title": "Procedure",
            "chunk_number": 0,
            "content": "Inspect BIN-DEMO-001, report the sensor fault, and escalate persistent failures.",
            "content_preview": "Inspect BIN-DEMO-001, report the sensor fault, and escalate persistent failures.",
            "vector_score": 0.8,
            "keyword_score": 0.4,
            "final_score": 0.7,
            "is_synthetic": True,
            "content_hash": "hash-1",
        }
        values.update(overrides)
        return RetrievedEvidence(**values)

    return factory
