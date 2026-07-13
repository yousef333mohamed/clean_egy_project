# Ingestion failure
## Symptoms
CSV/document jobs fail, stall, or report rejected rows.
## Impact
New data is unavailable; partial data must not become active.
## Initial checks
Use job/request ID to inspect safe error category, schema, hash, size, provider health and duplicate status.
## Safe response
Quarantine invalid input, do not retry permanent schema/content errors, and cancel only at a safe checkpoint.
## Escalation
Data/knowledge owner reviews source; security reviews malicious content/path attempts.
## Recovery
Correct source or configuration and enqueue a new idempotent job by stored reference.
## Verification
Confirm counts/hash/version, rejection report, active document state, retrieval/analytics checks and audit record.
## Post-incident actions
Record root cause, improve validation, and delete quarantined data per retention.
