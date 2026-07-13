# Database outage
## Symptoms
Readiness fails and database connections/timeouts rise.
## Impact
Operational, audit, prompt, job, and knowledge data cannot be served safely.
## Initial checks
Check managed status, network/TLS, capacity, pool exhaustion, locks and recent migrations without exposing connection strings.
## Safe response
Remove instances from readiness and stop ingestion/jobs. Do not serve stale operational data unless a reviewed cache exists.
## Escalation
Engage database/platform owners and incident command; security for integrity concerns.
## Recovery
Restore primary or fail over under the database plan, verify revision/integrity, then gradually resume workers.
## Verification
Run readiness, critical counts, audit continuity, smoke/evaluation tests and backup checks.
## Post-incident actions
Record RPO/RTO, cause, capacity/HA actions, and a fresh restore-tested backup.
