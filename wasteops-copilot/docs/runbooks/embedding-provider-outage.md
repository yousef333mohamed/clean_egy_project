# Embedding provider outage
## Symptoms
Query embedding or ingestion embedding fails.
## Impact
Semantic retrieval/ingestion is unavailable; existing documents remain stored.
## Initial checks
Check safe provider status, model/dimension configuration, quota, network, and partial ingestion runs.
## Safe response
Mark ingestion failed, not complete. Use only an approved compatible query embedding alternative; otherwise return retrieval unavailable.
## Escalation
Notify knowledge/provider owners and security for suspected compromise.
## Recovery
Resume idempotently from persisted references and verify dimension/hash/version consistency.
## Verification
Run retrieval/citation evaluation and confirm no duplicate or partial active document version.
## Post-incident actions
Review retry boundaries, concurrency, status messaging, and provider diversity.
