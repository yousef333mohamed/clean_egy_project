# Monitoring

Scrape `/internal/metrics` only from the private network with its dedicated token. Monitor request rate/latency/errors, auth failures/denials, limiting, DB/Redis health, queue depth/failures, provider latency/failure, insufficient-context and citation warnings, analytics/decision routing, and evaluation gates. Never label metrics with users, questions, document IDs, or request bodies.

Production logs are structured JSON with service, environment, request/trace ID, route, status, duration, subject hash, release, and safe error category. Scrub authorization/cookies, secrets, database URLs, prompts/responses, documents, embeddings, and result sets before any external error monitor. Test alerts in `deployment/monitoring/alerts.yml.example` and connect provider credentials only through its secret manager.
