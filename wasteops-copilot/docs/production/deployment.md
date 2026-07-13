# Deployment

1. Build and scan immutable SHA-tagged backend, worker, and frontend images.
2. Confirm quality/safety gates, current restore-tested backup, secrets, capacity, and rollback tag.
3. Back up PostgreSQL and original object storage.
4. Run `deployment/scripts/migrate.sh` once with the migration account; record Alembic revision.
5. Deploy via `deployment/scripts/deploy.sh`; application replicas never run Alembic.
6. Run readiness, smoke/evaluation checks, and verify metrics/alerts/log redaction.

Use expand-and-contract migrations so old and new application versions overlap safely. Resource limits begin from measured staging use; set CPU/memory reservations and worker concurrency in the target platform. TLS certificates are provisioned/renewed by the platform and mounted read-only as `wasteops_tls`.
