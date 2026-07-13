"""Orchestration for safe, auditable, chunked CSV ingestion."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.ingestion.bulk_writer import write_batch
from app.ingestion.csv_reader import CsvSchemaError, read_csv_chunks
from app.ingestion.file_discovery import discover_dataset
from app.ingestion.registry import DATASET_REGISTRY, DatasetDefinition, get_dataset
from app.ingestion.reports import RejectedRecord, json_safe_record, write_rejection_report
from app.ingestion.validators import RecordValidationError, convert_record
from app.models import IngestionError, IngestionRun, IngestionStatus
from app.schemas.ingestion import IngestionResult
from app.utils.file_hash import sha256_file


class IngestionService:
    """Ingest registry-approved files using one asynchronous database session."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        settings: Settings | None = None,
        batch_size: int | None = None,
        strict_columns: bool | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.batch_size = batch_size
        self.strict_columns = self.settings.ingestion_strict_columns if strict_columns is None else strict_columns
        self.raw_dir = Path(self.settings.data_dir) / "raw"
        self.rejected_dir = Path(self.settings.data_dir) / "rejected"
        self._parent_cache: dict[tuple[type, str], set[Any]] = {}

    async def _successful_run(self, dataset: str, file_hash: str) -> IngestionRun | None:
        statement = select(IngestionRun).where(
            IngestionRun.dataset_name == dataset,
            IngestionRun.file_hash == file_hash,
            IngestionRun.dry_run.is_(False),
            IngestionRun.status.in_([IngestionStatus.COMPLETED, IngestionStatus.COMPLETED_WITH_ERRORS]),
        )
        return (await self.session.scalars(statement)).first()

    async def _parent_ids(self, definition: DatasetDefinition) -> dict[str, set[Any]]:
        result: dict[str, set[Any]] = {}
        for foreign_key in definition.foreign_keys:
            cache_key = (foreign_key.parent_model, foreign_key.parent_column)
            if cache_key not in self._parent_cache:
                column = getattr(foreign_key.parent_model, foreign_key.parent_column)
                self._parent_cache[cache_key] = set((await self.session.scalars(select(column))).all())
            result[foreign_key.column] = self._parent_cache[cache_key]
        return result

    async def _record_errors(self, run: IngestionRun, rejected: list[RejectedRecord]) -> None:
        if not rejected:
            return
        for offset in range(0, len(rejected), 1000):
            self.session.add_all(
                [
                    IngestionError(
                        ingestion_run_id=run.id,
                        dataset_name=run.dataset_name,
                        source_filename=run.source_filename,
                        row_number=item.row_number,
                        error_code=item.error_code,
                        error_message=item.error_message,
                        raw_record=item.raw_record,
                    )
                    for item in rejected[offset : offset + 1000]
                ]
            )
            await self.session.commit()

    @staticmethod
    def _result(run: IngestionRun, warnings: list[str], rejection_report: Path | None = None) -> IngestionResult:
        completed = run.completed_at or datetime.now(UTC)
        return IngestionResult(
            run_id=run.id,
            dataset=run.dataset_name,
            source_filename=run.source_filename,
            status=run.status,
            dry_run=run.dry_run,
            total_rows=run.total_rows,
            valid_rows=run.valid_rows,
            inserted_rows=run.inserted_rows,
            duplicate_rows=run.duplicate_rows,
            rejected_rows=run.rejected_rows,
            failed_rows=run.failed_rows,
            warnings=warnings,
            rejection_report=str(rejection_report) if rejection_report else None,
            started_at=run.started_at,
            completed_at=completed,
            duration_seconds=max(0.0, (completed - run.started_at).total_seconds()),
            error_message=run.error_message,
        )

    async def ingest_dataset(self, dataset_name: str, *, dry_run: bool = False, force: bool = False) -> IngestionResult:
        """Discover, validate, and optionally persist one registered dataset."""
        definition = get_dataset(dataset_name)
        discovered = discover_dataset(self.raw_dir, definition)
        if not discovered.available or discovered.path is None or discovered.filename is None:
            raise FileNotFoundError(f"No approved CSV file found for dataset {dataset_name!r}")

        started = datetime.now(UTC)
        file_hash = sha256_file(discovered.path)
        existing = await self._successful_run(dataset_name, file_hash)
        if existing is not None and not force and not dry_run:
            skipped = IngestionRun(
                dataset_name=dataset_name,
                source_filename=discovered.filename,
                file_hash=file_hash,
                file_size_bytes=discovered.size_bytes or 0,
                status=IngestionStatus.SKIPPED_DUPLICATE,
                started_at=started,
                completed_at=datetime.now(UTC),
                total_rows=existing.total_rows,
                valid_rows=existing.valid_rows,
                inserted_rows=0,
                duplicate_rows=existing.valid_rows,
                rejected_rows=0,
                failed_rows=0,
                dry_run=False,
                metadata_json={"duplicate_of_run_id": str(existing.id)},
            )
            self.session.add(skipped)
            await self.session.commit()
            return self._result(skipped, ["This dataset/file hash was already successfully ingested."])

        run = IngestionRun(
            dataset_name=dataset_name,
            source_filename=discovered.filename,
            file_hash=file_hash,
            file_size_bytes=discovered.size_bytes or 0,
            status=IngestionStatus.RUNNING,
            started_at=started,
            total_rows=0,
            valid_rows=0,
            inserted_rows=0,
            duplicate_rows=0,
            rejected_rows=0,
            failed_rows=0,
            dry_run=dry_run,
            metadata_json={"force": force},
        )
        self.session.add(run)
        await self.session.commit()

        warnings: list[str] = []
        rejected: list[RejectedRecord] = []
        seen_keys: set[tuple[Any, ...]] = set()
        overload_warnings = 0
        truck_capacities: dict[Any, Any] = {}
        try:
            parent_ids = await self._parent_ids(definition)
            if definition.name == "truck_trip_logs":
                parent = definition.foreign_keys[0].parent_model
                rows = await self.session.execute(select(parent.truck_id, parent.capacity_kg))
                truck_capacities = dict(rows.all())
            batch_size = self.batch_size or min(self.settings.csv_batch_size, definition.batch_size)
            schema, chunks = read_csv_chunks(discovered.path, definition, batch_size, strict_columns=self.strict_columns)
            warnings.extend(schema.warnings)
            for chunk in chunks:
                pending: list[dict[str, Any]] = []
                pending_source: list[tuple[int, dict[str, Any]]] = []
                for row in chunk.to_dict(orient="records"):
                    row_number = int(row.pop("__source_row_number__"))
                    raw = json_safe_record(row)
                    run.total_rows += 1
                    try:
                        record = convert_record(row, definition, self.settings.source_timezone)
                        for column, allowed_values in parent_ids.items():
                            if record[column] not in allowed_values:
                                raise RecordValidationError("FOREIGN_KEY_NOT_FOUND", f"{column} does not reference an existing parent")
                        run.valid_rows += 1
                        natural_key = tuple(record[column] for column in definition.natural_key)
                        if natural_key in seen_keys:
                            run.duplicate_rows += 1
                            continue
                        seen_keys.add(natural_key)
                        if definition.name == "truck_trip_logs" and record["truck_id"] in truck_capacities:
                            overload_warnings += int(record["load_kg"] > truck_capacities[record["truck_id"]])
                    except RecordValidationError as exc:
                        rejected.append(RejectedRecord(row_number, exc.code, str(exc), raw))
                        run.rejected_rows += 1
                        continue
                    pending.append(record)
                    pending_source.append((row_number, raw))

                if definition.name in {"smart_bins", "trucks", "workforce"}:
                    identifier = definition.natural_key[0]
                    self._parent_cache.setdefault((definition.model, identifier), set()).update(record[identifier] for record in pending)

                if not dry_run and pending:
                    outcome = await write_batch(self.session, definition, pending)
                    run.inserted_rows += outcome.inserted
                    run.duplicate_rows += outcome.duplicates
                    for index, message in outcome.failures:
                        row_number, raw = pending_source[index]
                        rejected.append(RejectedRecord(row_number, "DATABASE_ERROR", message, raw))
                        run.failed_rows += 1

            if definition.expected_rows is not None and run.total_rows != definition.expected_rows:
                warnings.append(f"Source row count {run.total_rows} differs from the reference count {definition.expected_rows}.")
            if overload_warnings:
                warnings.append(f"{overload_warnings} trip rows have load_kg above registered truck capacity; records were preserved.")
            if definition.name in {"smart_bins", "trucks", "workforce"} and not dry_run:
                identifier = definition.natural_key[0]
                column = getattr(definition.model, identifier)
                self._parent_cache[(definition.model, identifier)] = set((await self.session.scalars(select(column))).all())
            report = write_rejection_report(self.rejected_dir, dataset_name, run.id, rejected)
            await self._record_errors(run, rejected)
            run.completed_at = datetime.now(UTC)
            if dry_run:
                run.status = IngestionStatus.DRY_RUN_COMPLETED
            elif existing is not None and force:
                run.status = IngestionStatus.SKIPPED_DUPLICATE
                warnings.append("Force processed the file safely; existing natural keys were retained.")
            elif run.rejected_rows or run.failed_rows:
                run.status = IngestionStatus.COMPLETED_WITH_ERRORS
            else:
                run.status = IngestionStatus.COMPLETED
            run.metadata_json = {"force": force, "warnings": warnings, "rejection_report": str(report) if report else None}
            await self.session.commit()
            return self._result(run, warnings, report)
        except CsvSchemaError as exc:
            await self.session.rollback()
            run = await self.session.get(IngestionRun, run.id)
            assert run is not None
            run.status = IngestionStatus.FAILED
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)
            await self.session.commit()
            return self._result(run, warnings)
        except Exception as exc:
            await self.session.rollback()
            failed_run = await self.session.get(IngestionRun, run.id)
            if failed_run is not None:
                failed_run.status = IngestionStatus.FAILED
                failed_run.error_message = f"{type(exc).__name__}: ingestion could not continue"
                failed_run.completed_at = datetime.now(UTC)
                await self.session.commit()
            raise

    async def ingest_all(self, *, dry_run: bool = False, force: bool = False) -> list[IngestionResult]:
        """Ingest all available datasets in parent-before-child order."""
        results: list[IngestionResult] = []
        for definition in sorted(DATASET_REGISTRY.values(), key=lambda item: item.ingestion_order):
            discovered = discover_dataset(self.raw_dir, definition)
            if discovered.available:
                results.append(await self.ingest_dataset(definition.name, dry_run=dry_run, force=force))
        return results
