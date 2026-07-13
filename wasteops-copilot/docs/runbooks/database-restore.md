# Database restore
## Symptoms
Recovery or periodic restore verification is authorized.
## Impact
Restoring over the wrong target can destroy data.
## Initial checks
Confirm incident command, isolated target, artifact checksum/key, RPO/RTO, object-file backup, and target emptiness.
## Safe response
Set the explicit restore confirmation and run `restore.sh` against an isolated target first.
## Escalation
Database owner approves any production cutover; security owns suspected backup theft.
## Recovery
Validate schema/data, place service in maintenance, switch connections through change control, retain old database read-only.
## Verification
Check Alembic revision, critical counts, audit continuity, smoke/evaluation tests and application readiness.
## Post-incident actions
Record artifact hash, timings, evidence, destruction of test data, and RPO/RTO findings.
