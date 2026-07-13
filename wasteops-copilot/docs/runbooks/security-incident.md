# Security incident
## Symptoms
Token/secret leakage, privilege abuse, malicious ingestion, unusual denials, data access, or supply-chain alert.
## Impact
Confidentiality, integrity, availability, and decision trust may be affected.
## Initial checks
Activate incident command, preserve immutable logs/audit/build evidence, scope identities/releases/data, and avoid exposing secrets in tickets.
## Safe response
Contain affected identities/services, revoke sessions, rotate scoped secrets, quarantine inputs/images, and fail closed. Do not destroy evidence.
## Escalation
Immediately notify security, legal/privacy, service/data owners and required regulators under policy.
## Recovery
Use clean signed images and rotated credentials, validate DB/object/backup integrity, restore if approved, and recertify access.
## Verification
Run auth/RBAC/security/safety/scans/smoke tests and monitor for recurrence.
## Post-incident actions
Complete timeline, impact/notifications, root cause, threat-model/runbook updates and tracked remediations.
