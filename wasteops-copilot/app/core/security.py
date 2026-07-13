"""SQL safety controls."""

import re

from app.utils.exceptions import UnsafeQueryError

_FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|COPY|CALL|DO)\b", re.I)


def validate_read_only_sql(query: str, row_limit: int = 200) -> str:
    """Validate one SELECT/WITH statement and enforce a maximum result size."""
    cleaned = query.strip().rstrip(";").strip()
    if not cleaned or ";" in cleaned or not re.match(r"^(SELECT|WITH)\b", cleaned, re.I):
        raise UnsafeQueryError("Only one SELECT or WITH query is allowed")
    if _FORBIDDEN.search(cleaned) or re.search(r"--|/\*|\*/", cleaned):
        raise UnsafeQueryError("Query contains a forbidden SQL token")
    # The outer cap cannot be bypassed by a model-generated excessive LIMIT.
    return f"SELECT * FROM (\n{cleaned}\n) AS wasteops_safe_query\nLIMIT {row_limit}"
