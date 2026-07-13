"""Validation helpers for opaque operational identifiers and filter text."""

import re

SAFE_VALUE = re.compile(r"^[\w\- .,/&\u0600-\u06ff]+$", re.UNICODE)
SQL_TOKENS = re.compile(r"(;|--|/\*|\*/|\b(select|insert|update|delete|drop|alter|create|grant|revoke|union)\b)", re.IGNORECASE)


def validate_safe_value(value: str) -> str:
    """Preserve Unicode/IDs while rejecting SQL-like control text."""
    normalized = value.strip()
    if not normalized or len(normalized) > 160 or SQL_TOKENS.search(normalized) or not SAFE_VALUE.fullmatch(normalized):
        raise ValueError("filter contains unsupported or unsafe characters")
    return normalized
