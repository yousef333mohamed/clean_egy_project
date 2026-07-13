# Deployment
## Symptoms
A release is approved and ready to promote.
## Impact
Incorrect sequencing can cause downtime or incompatible schema use.
## Initial checks
Confirm image digests, quality/safety gates, backup/restore evidence, secrets, capacity, migration plan, and rollback tag.
## Safe response
Run one backup, one migration job, immutable deployment, readiness and smoke tests. Stop if any gate fails.
## Escalation
Notify service owner, database owner, security, and incident commander for unexpected changes.
## Recovery
Roll application back; forward-fix schema or restore only under the database plan.
## Verification
Check release/version and Alembic revision, key routes, jobs, metrics, logs, and alerts.
## Post-incident actions
Record timings, approvers, revisions, failures, and corrective actions.
