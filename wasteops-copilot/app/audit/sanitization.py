"""One-way minimization for audit identifiers."""

import hashlib


def safe_hash(value: str | None) -> str | None:
    """Hash a value so logs remain correlatable without storing raw identity data."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None


def safe_details(values: dict[str, object]) -> dict[str, object]:
    """Allow only bounded scalar metadata."""
    return {key: value for key, value in values.items() if isinstance(value, (bool, int, float)) or (isinstance(value, str) and len(value) <= 200)}
