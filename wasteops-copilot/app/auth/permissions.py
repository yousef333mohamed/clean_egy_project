"""Central role-to-permission policy."""

from app.auth.enums import Permission, Role

P = Permission
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset({P.DASHBOARD_READ, P.ANALYTICS_READ, P.DOCUMENTS_READ}),
    Role.OPERATOR: frozenset({P.DASHBOARD_READ, P.ANALYTICS_READ, P.DOCUMENTS_READ, P.ASSISTANT_USE, P.FEEDBACK_CREATE}),
    Role.MANAGER: frozenset(
        {P.DASHBOARD_READ, P.ANALYTICS_READ, P.DOCUMENTS_READ, P.ASSISTANT_USE, P.FEEDBACK_CREATE, P.DECISIONS_REQUEST, P.DECISIONS_PREVIEW}
    ),
    Role.DATA_ENGINEER: frozenset({P.DASHBOARD_READ, P.DATASETS_READ, P.DATASETS_VALIDATE, P.DATASETS_INGEST, P.ANALYTICS_READ}),
    Role.KNOWLEDGE_MANAGER: frozenset({P.DOCUMENTS_READ, P.DOCUMENTS_INGEST, P.DOCUMENTS_MANAGE, P.ASSISTANT_USE}),
    Role.PROMPT_ADMIN: frozenset({P.PROMPTS_READ, P.PROMPTS_CREATE, P.PROMPTS_ACTIVATE, P.PROMPTS_ARCHIVE, P.EVALUATIONS_READ, P.EVALUATIONS_RUN}),
    Role.AUDITOR: frozenset({P.DASHBOARD_READ, P.ANALYTICS_READ, P.EVALUATIONS_READ, P.TRACES_READ, P.FEEDBACK_READ, P.AUDIT_READ}),
    Role.SYSTEM_ADMIN: frozenset(Permission),
}


def permissions_for_roles(roles: set[str]) -> set[str]:
    """Return permissions for recognized roles; unknown roles grant nothing."""
    output: set[str] = set()
    for value in roles:
        try:
            output.update(permission.value for permission in ROLE_PERMISSIONS[Role(value)])
        except (ValueError, KeyError):
            continue
    return output
