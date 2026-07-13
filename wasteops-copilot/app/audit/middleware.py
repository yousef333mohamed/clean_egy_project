"""Best-effort HTTP audit capture; explicit domain audits may add richer events."""

from app.audit.sanitization import safe_hash


def audit_values(request, response) -> dict[str, object] | None:
    """Create sanitized metadata for security-sensitive requests."""
    if not request.app.state.settings.auth_enabled:
        return None
    sensitive = response.status_code in {401, 403} or request.method in {"POST", "PUT", "PATCH", "DELETE"}
    if not sensitive:
        return None
    user = getattr(request.state, "authenticated_user", None)
    return {
        "event_type": "authorization.denial" if response.status_code == 403 else "http.mutation",
        "actor_subject_hash": safe_hash(user.subject) if user else None,
        "actor_roles": sorted(user.roles) if user else [],
        "request_id": getattr(request.state, "request_id", None),
        "route": request.url.path[:255],
        "method": request.method,
        "status_code": response.status_code,
        "resource_type": None,
        "resource_id_hash": None,
        "source_ip_hash": safe_hash(request.client.host if request.client else None),
        "details": {},
    }
