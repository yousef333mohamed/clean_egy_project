"""Required model-card generation."""

from pathlib import Path


SECTIONS = (
    "Model purpose",
    "Business use",
    "Not intended for",
    "Training period",
    "Feature list",
    "Target definition",
    "Data split",
    "Metrics",
    "Threshold",
    "Known limitations",
    "Data-quality risks",
    "Leakage checks",
    "Subgroup performance",
    "Human oversight",
    "Rollback procedure",
    "Model version",
    "Approval status",
)


def generate_model_card(path: Path, values: dict[str, object]) -> Path:
    missing = [section for section in SECTIONS if section not in values]
    if missing:
        raise ValueError(f"Model card fields missing: {missing}")
    path.parent.mkdir(parents=True, exist_ok=True)
    content = [f"# {values['Model purpose']}", ""]
    for section in SECTIONS[1:]:
        content.extend([f"## {section}", "", str(values[section]), ""])
    path.write_text("\n".join(content), encoding="utf-8")
    return path
