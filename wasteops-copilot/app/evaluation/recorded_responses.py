"""Explicitly updated, sanitized provider fixtures for offline regressions."""

import json
from pathlib import Path
from typing import Any

from app.observability.sanitization import sanitize


class RecordedResponseStore:
    def __init__(self, directory: Path = Path("tests/fixtures/recorded")) -> None:
        self.directory = directory

    def save(self, fixture_name: str, response: dict[str, Any], *, model: str, prompt_key: str, prompt_version: str, update: bool = False) -> Path:
        safe_name = Path(fixture_name).name
        if safe_name != fixture_name or not safe_name.endswith(".json"):
            raise ValueError("Recorded fixture name must be a JSON basename")
        path = self.directory / safe_name
        if path.exists() and not update:
            raise FileExistsError("Recorded fixtures are never overwritten without update=True")
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = sanitize({"provider": {"model": model}, "prompt": {"key": prompt_key, "version": prompt_version}, "response": response})
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def load(self, fixture_name: str) -> dict[str, Any]:
        path = self.directory / Path(fixture_name).name
        return json.loads(path.read_text(encoding="utf-8"))
