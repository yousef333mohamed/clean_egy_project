"""Strict claim extraction."""

from typing import Any

from fastapi import HTTPException, status


def string_set_claim(payload: dict[str, Any], name: str) -> set[str]:
    """Read a string array claim and reject ambiguous shapes."""
    value = payload.get(name, [])
    if value is None:
        return set()
    if isinstance(value, str):
        values = value.split()
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        values = value
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token contains malformed authorization claims")
    return {item for item in values if item and len(item) <= 255}
