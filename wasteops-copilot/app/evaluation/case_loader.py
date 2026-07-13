"""Strict versioned JSON evaluation dataset loading."""

import json
from pathlib import Path

from app.schemas.evaluation import EvaluationCase, EvaluationDataset


class CaseLoader:
    def load(self, path: Path) -> EvaluationDataset:
        if not path.is_file() or path.suffix.casefold() != ".json":
            raise ValueError(f"Evaluation dataset not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            cases = payload
            name, version, evaluation_type = path.stem, "1.0.0", path.parent.name
        elif isinstance(payload, dict):
            cases = payload.get("cases", [])
            name = payload.get("name", path.stem)
            version = payload.get("version", "1.0.0")
            evaluation_type = payload.get("evaluation_type", path.parent.name)
        else:
            raise ValueError("Dataset root must be an object or array")
        if not cases:
            raise ValueError("Evaluation dataset contains no cases")
        parsed = [EvaluationCase.model_validate(case) for case in cases]
        ids = [case.case_id for case in parsed]
        if len(ids) != len(set(ids)):
            raise ValueError("Evaluation case IDs must be unique")
        return EvaluationDataset(name=name, version=version, evaluation_type=evaluation_type, cases=parsed, path=path)
