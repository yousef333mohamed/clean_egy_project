"""Filesystem registry adapter with fixed model names and safe metadata only."""

from pathlib import Path

from app.registry.model_metadata import ModelMetadata

ALLOWED_MODELS = frozenset({"bin-overflow", "collection-priority", "truck-anomaly", "missed-collection", "workforce-forecast"})


class ModelRegistry:
    def __init__(self, artifact_directory: Path) -> None:
        self.root = artifact_directory.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def metadata_path(self, model_name: str, version: str) -> Path:
        if model_name not in ALLOWED_MODELS or not version.replace("-", "").replace(".", "").isalnum():
            raise ValueError("Unsupported model name or version")
        path = (self.root / model_name / version / "metadata.json").resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid registry path")
        return path

    def get(self, model_name: str, version: str) -> ModelMetadata:
        return ModelMetadata.model_validate_json(self.metadata_path(model_name, version).read_text(encoding="utf-8"))

    def save(self, metadata: ModelMetadata) -> None:
        path = self.metadata_path(metadata.model_name, metadata.version)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

    def active(self) -> list[ModelMetadata]:
        result = []
        for path in self.root.glob("*/*/metadata.json"):
            metadata = ModelMetadata.model_validate_json(path.read_text(encoding="utf-8"))
            if metadata.stage == "Production":
                result.append(metadata)
        return sorted(result, key=lambda item: item.model_name)

    def describe(self, model_name: str) -> list[ModelMetadata]:
        if model_name not in ALLOWED_MODELS:
            raise ValueError("Unsupported model name")
        return sorted(
            (ModelMetadata.model_validate_json(path.read_text(encoding="utf-8")) for path in (self.root / model_name).glob("*/metadata.json")),
            key=lambda item: item.created_at,
            reverse=True,
        )
