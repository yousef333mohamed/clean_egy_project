"""Checksum-verified loading of locally registered, approved joblib artifacts."""

import hashlib

import joblib

from app.registry.model_metadata import ModelMetadata
from app.registry.model_registry import ModelRegistry


class ModelLoadError(RuntimeError):
    pass


class ModelLoader:
    def __init__(self, registry: ModelRegistry, allowed_checksums: set[str] | None = None) -> None:
        self.registry = registry
        self.allowed_checksums = allowed_checksums or set()

    def load(self, metadata: ModelMetadata):
        if metadata.stage != "Production" or metadata.approval_status != "approved":
            raise ModelLoadError("Only approved Production models may serve predictions")
        artifact = (self.registry.root / metadata.artifact_file).resolve()
        if self.registry.root not in artifact.parents or not artifact.is_file():
            raise ModelLoadError("Registered artifact is unavailable")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != metadata.artifact_sha256 or (self.allowed_checksums and digest not in self.allowed_checksums):
            raise ModelLoadError("Artifact checksum validation failed")
        model = joblib.load(artifact)
        if getattr(model, "model_name", None) != metadata.model_name or getattr(model, "model_version", None) != metadata.version:
            raise ModelLoadError("Model artifact identity does not match registry metadata")
        return model
