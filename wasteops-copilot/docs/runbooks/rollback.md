# Rollback
## Symptoms
Smoke tests, readiness, safety gates, or error rates regress after deployment.
## Impact
Users may receive errors or unsafe/incomplete answers.
## Initial checks
Compare release metadata, logs, metrics, schema compatibility, and provider status; preserve evidence.
## Safe response
Pause rollout and use `rollback.sh` with the last tested immutable tag. Never auto-downgrade PostgreSQL.
## Escalation
Engage application/database owners and security if data or authorization is affected.
## Recovery
Restore service with the previous application; use a reviewed forward migration or isolated database restore if required.
## Verification
Run readiness, smoke and safety tests and verify monitoring returns to baseline.
## Post-incident actions
Document cause, affected revisions, data checks, and prevention.
