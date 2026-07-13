"""Allow-listed, parameterized SQLAlchemy metadata filtering."""

from typing import Any

from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement

from app.models import DocumentStatus, KnowledgeDocument
from app.schemas.retrieval import RetrievalFilters


def _casefold_filter(column: Any, values: list[str]) -> ColumnElement[bool]:
    return func.lower(column).in_([value.casefold() for value in values])


def build_metadata_conditions(filters: RetrievalFilters | None) -> list[ColumnElement[bool]]:
    """Build active/successful constraints plus explicitly supplied filters."""
    conditions: list[ColumnElement[bool]] = [
        KnowledgeDocument.is_active.is_(True),
        KnowledgeDocument.status.in_([DocumentStatus.COMPLETED, DocumentStatus.COMPLETED_WITH_WARNINGS]),
    ]
    if filters is None:
        return conditions
    mapping = {
        "document_type": KnowledgeDocument.document_type,
        "department": KnowledgeDocument.department,
        "asset_type": KnowledgeDocument.asset_type,
        "region": KnowledgeDocument.region,
        "language": KnowledgeDocument.language,
        "version": KnowledgeDocument.version,
        "source_filename": KnowledgeDocument.source_filename,
    }
    for name, column in mapping.items():
        values = getattr(filters, name)
        if values is not None:
            conditions.append(_casefold_filter(column, values))
    if filters.effective_date_from is not None:
        conditions.append(KnowledgeDocument.effective_date >= filters.effective_date_from)
    if filters.effective_date_to is not None:
        conditions.append(KnowledgeDocument.effective_date <= filters.effective_date_to)
    if filters.is_synthetic is not None:
        conditions.append(KnowledgeDocument.is_synthetic.is_(filters.is_synthetic))
    return conditions


def normalized_filters(filters: RetrievalFilters | None) -> dict[str, Any]:
    return filters.applied() if filters else {}
