"""Safe discovery of canonical CSV files and their uploaded aliases."""

from dataclasses import dataclass
from pathlib import Path

from app.ingestion.registry import DATASET_REGISTRY, DatasetDefinition


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    """A registry-approved source file."""

    dataset: str
    filename: str | None
    size_bytes: int | None
    available: bool
    path: Path | None = None


def discover_dataset(raw_dir: Path, definition: DatasetDefinition) -> DiscoveredFile:
    """Resolve only allow-listed basenames inside *raw_dir*."""
    root = raw_dir.resolve()
    for filename in definition.filenames:
        candidate = (root / filename).resolve()
        if candidate.parent == root and candidate.is_file():
            return DiscoveredFile(definition.name, filename, candidate.stat().st_size, True, candidate)
    return DiscoveredFile(definition.name, None, None, False, None)


def discover_files(raw_dir: Path) -> list[DiscoveredFile]:
    """Return availability in dependency order."""
    definitions = sorted(DATASET_REGISTRY.values(), key=lambda item: item.ingestion_order)
    return [discover_dataset(raw_dir, definition) for definition in definitions]
