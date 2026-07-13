from datetime import datetime, timezone
from pathlib import Path
import hashlib, joblib, pytest
from app.models.overflow_model import OverflowModel
from app.registry.model_metadata import ModelMetadata
from app.registry.model_registry import ModelRegistry
from app.registry.promotion_service import PromotionRejected, PromotionService
from app.inference.model_loader import ModelLoader, ModelLoadError


def metadata(tmp_path, **changes):
    artifact = tmp_path / "bin-overflow" / "1" / "model.joblib"
    artifact.parent.mkdir(parents=True)
    model = OverflowModel(version="1")
    joblib.dump(model, artifact)
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    card = tmp_path / "card.md"
    card.write_text("card")
    values = dict(
        model_name="bin-overflow",
        version="1",
        stage="None",
        training_period_start="2026-01-01",
        training_period_end="2026-02-01",
        feature_version="1.0.0",
        code_commit="abc",
        artifact_file="bin-overflow/1/model.joblib",
        artifact_sha256=digest,
        approval_status="approved",
        created_at=datetime.now(timezone.utc),
        leakage_checks_passed=True,
        validation_passed=True,
        baseline_comparison_passed=True,
        calibration_acceptable=True,
        critical_subgroup_failure=False,
        model_card_file=str(card),
    )
    values.update(changes)
    return ModelMetadata(**values)


def test_promotion_requires_all_quality_gates(tmp_path):
    registry = ModelRegistry(tmp_path)
    item = metadata(tmp_path, leakage_checks_passed=False)
    registry.save(item)
    with pytest.raises(PromotionRejected):
        PromotionService(registry).promote("bin-overflow", "1", "Production", approved_by="human")


def test_promotion_and_checksum_verified_loading(tmp_path):
    registry = ModelRegistry(tmp_path)
    item = metadata(tmp_path)
    registry.save(item)
    PromotionService(registry).promote("bin-overflow", "1", "Production", approved_by="human")
    active = registry.get("bin-overflow", "1")
    loaded = ModelLoader(registry, {active.artifact_sha256}).load(active)
    assert loaded.model_version == "1"
    Path(tmp_path / active.artifact_file).write_bytes(b"tampered")
    with pytest.raises(ModelLoadError):
        ModelLoader(registry).load(active)
