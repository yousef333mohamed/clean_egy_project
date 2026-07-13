"""Cached UTF-8 prompt-template loading from the application package."""

from functools import lru_cache
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


@lru_cache(maxsize=16)
def load_prompt(filename: str) -> str:
    """Load an allow-listed prompt basename without path traversal."""
    if Path(filename).name != filename or not filename.endswith(".txt"):
        raise ValueError("Prompt filename is invalid")
    path = PROMPT_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Prompt not found: {filename}")
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Prompt is empty: {filename}")
    return content
