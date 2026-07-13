# Redis outage
## Symptoms
Rate-limit/queue health fails or queue depth stops changing.
## Impact
Production readiness fails when Redis is required; jobs pause and distributed limiting is unavailable.
## Initial checks
Check private connectivity, authentication, memory/eviction, latency and recent changes without printing the URL.
## Safe response
Keep Redis-required API instances unready and pause producers/workers. Do not treat local limiter fallback as distributed protection.
## Escalation
Notify platform/application owners and security for exposure/credential concerns.
## Recovery
Restore Redis, rotate password if needed, validate key prefix/expiry, then resume workers at limited concurrency.
## Verification
Test limit 429, enqueue/status, queue depth, job idempotency and readiness.
## Post-incident actions
Review sizing, isolation, failover and lost disposable state.
