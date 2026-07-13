"""Explicit, human-authorized model promotion quality gate."""

from datetime import datetime, timezone
from pathlib import Path

from app.registry.model_registry import ModelRegistry


class PromotionRejected(ValueError):
    pass


class PromotionService:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def promote(self, model_name: str, version: str, stage: str, *, approved_by: str) -> None:
        if stage not in {"Staging", "Production", "Archived"}:
            raise PromotionRejected("Unsupported promotion stage")
        if not approved_by.strip():
            raise PromotionRejected("Approval identity is required")
        metadata = self.registry.get(model_name, version)
        checks = {
            "validation": metadata.validation_passed,
            "leakage": metadata.leakage_checks_passed,
            "baseline comparison": metadata.baseline_comparison_passed,
            "calibration": metadata.calibration_acceptable,
            "subgroup safety": not metadata.critical_subgroup_failure,
            "approval": metadata.approval_status == "approved",
            "model card": bool(metadata.model_card_file and Path(metadata.model_card_file).is_file()),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise PromotionRejected(f"Promotion quality gate failed: {', '.join(failed)}")
        updated = metadata.model_copy(update={"stage": stage, "promoted_at": datetime.now(timezone.utc), "promoted_by": approved_by})
        self.registry.save(updated)
