"""Input normalization helpers."""

import re


def normalize_column_name(value: str) -> str:
    """Convert a CSV heading into lower snake_case."""
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", value.strip())).strip("_").lower()
