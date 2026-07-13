# Secret rotation
## Symptoms
Scheduled rotation, personnel/provider change, or suspected exposure.
## Impact
Poor sequencing can interrupt identity, database, Redis, storage, or model access.
## Initial checks
Inventory consumers/owners, overlap capability, current version references, rollback and exposure scope—never retrieve values into logs.
## Safe response
Create a new secret in the manager, grant least privilege, deploy references, verify, revoke old value, then remove it.
## Escalation
Security leads emergency compromise rotation; provider/database owners approve disruptive changes.
## Recovery
OIDC: overlap client secrets and test callback. Database: create/alter credential, update pools, revoke old sessions. LLM: issue scoped key, deploy workers/API, revoke old. Redis/storage follow the same overlap pattern.
## Verification
Test sign-in, readiness, jobs, storage, provider calls, audits and scans; confirm old credential fails.
## Post-incident actions
Record secret version/time/owner—not value—update expiry alerts and investigate any exposure.
