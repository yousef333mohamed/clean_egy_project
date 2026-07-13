"""Metadata schema normalization and SQL condition tests."""

from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.retrieval.metadata_filters import build_metadata_conditions
from app.schemas.retrieval import RetrievalFilters


def test_single_lists_dates_combined_and_case_handling() -> None:
    filters = RetrievalFilters(
        document_type="Operational_SOP",
        asset_type=["smart_bin", "truck"],
        effective_date_from=date(2025, 1, 1),
        effective_date_to=date(2026, 12, 31),
        is_synthetic=True,
    )
    assert filters.document_type == ["Operational_SOP"]
    conditions = build_metadata_conditions(filters)
    sql = " AND ".join(str(item.compile(dialect=postgresql.dialect())) for item in conditions)
    assert "lower(knowledge_documents.document_type)" in sql
    assert "knowledge_documents.is_active IS true" in sql
    assert "knowledge_documents.is_synthetic IS true" in sql
    assert "effective_date" in sql


def test_unsupported_and_invalid_date_filters_are_rejected() -> None:
    with pytest.raises(ValidationError):
        RetrievalFilters(unsupported="x")
    with pytest.raises(ValidationError):
        RetrievalFilters(effective_date_from="2026-02-01", effective_date_to="2026-01-01")
