"""PostgreSQL batch inserts with conflict counting and failure isolation."""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.ingestion.registry import DatasetDefinition

logger = get_logger(__name__)


@dataclass(slots=True)
class BatchWriteResult:
    """Outcome of one database batch."""

    inserted: int = 0
    duplicates: int = 0
    failures: list[tuple[int, str]] = field(default_factory=list)


async def _insert_records(session: AsyncSession, definition: DatasetDefinition, records: list[dict[str, Any]]) -> int:
    statement = insert(definition.model).values(records)
    statement = statement.on_conflict_do_nothing(index_elements=list(definition.natural_key)).returning(
        *[definition.model.__table__.c[key] for key in definition.natural_key]
    )
    result = await session.execute(statement)
    return len(result.fetchall())


async def write_batch(session: AsyncSession, definition: DatasetDefinition, records: list[dict[str, Any]]) -> BatchWriteResult:
    """Insert a batch, retrying individually if a database error affects it."""
    if not records:
        return BatchWriteResult()
    try:
        async with session.begin_nested():
            inserted = await _insert_records(session, definition, records)
        await session.commit()
        return BatchWriteResult(inserted=inserted, duplicates=len(records) - inserted)
    except Exception:
        logger.exception("ingestion_batch_insert_failed", dataset=definition.name, batch_rows=len(records))
        await session.rollback()

    outcome = BatchWriteResult()
    for index, record in enumerate(records):
        try:
            async with session.begin_nested():
                inserted = await _insert_records(session, definition, [record])
            await session.commit()
            outcome.inserted += inserted
            outcome.duplicates += 1 - inserted
        except Exception as exc:
            logger.exception("ingestion_row_insert_failed", dataset=definition.name, batch_index=index)
            await session.rollback()
            outcome.failures.append((index, f"{type(exc).__name__}: database rejected record"))
    return outcome
