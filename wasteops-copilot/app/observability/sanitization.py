"""Recursive bounded redaction for traces, reports, and feedback."""

import re
from collections.abc import Mapping, Sequence
from typing import Any

MAX_STRING_LENGTH = 1000
MAX_COLLECTION_ITEMS = 50
REDACTED = "[REDACTED]"
SENSITIVE_KEYS = re.compile(r"(?:api[-_]?key|authorization|password|passwd|secret|token|database[_-]?url|credential|embedding|sql)", re.I)
SENSITIVE_VALUES = (
    re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)(?:sk|key)-[a-z0-9_-]{12,}"),
    re.compile(r"(?i)(?:postgres(?:ql)?|mysql|mongodb)(?:\+\w+)?://[^\s]+"),
    re.compile(r"(?i)(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
)


def sanitize_text(value: str, *, max_length: int = MAX_STRING_LENGTH, reject_html: bool = False) -> str:
    """Redact common credentials and bound text, marking truncation explicitly."""
    text = re.sub(r"<[^>]*>", "", value) if reject_html else value
    for pattern in SENSITIVE_VALUES:
        text = pattern.sub(REDACTED, text)
    if len(text) > max_length:
        return f"{text[:max_length]}… [TRUNCATED original_chars={len(text)}]"
    return text


def sanitize(value: Any, *, max_string_length: int = MAX_STRING_LENGTH) -> Any:
    """Sanitize JSON-like values without serializing arbitrary private objects."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return sanitize_text(value, max_length=max_string_length)
    if isinstance(value, Mapping):
        clean: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_COLLECTION_ITEMS:
                clean["_truncated"] = True
                break
            key_text = str(key)[:100]
            clean[key_text] = REDACTED if SENSITIVE_KEYS.search(key_text) else sanitize(item, max_string_length=max_string_length)
        return clean
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        clean_list = [sanitize(item, max_string_length=max_string_length) for item in value[:MAX_COLLECTION_ITEMS]]
        if len(value) > MAX_COLLECTION_ITEMS:
            clean_list.append({"_truncated": True, "original_items": len(value)})
        return clean_list
    return sanitize_text(type(value).__name__, max_length=max_string_length)


def contains_sensitive_data(value: Any) -> bool:
    """Conservative security assertion used by fixture and trace tests."""
    serialized = str(value)
    return bool(SENSITIVE_KEYS.search(serialized) or any(pattern.search(serialized) for pattern in SENSITIVE_VALUES))
