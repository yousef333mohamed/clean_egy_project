# Known limitations before go-live

- Live OIDC sign-in, logout, refresh, IdP key rotation, and every external role mapping require a configured test identity provider; local tests use generated RSA keys and never real secrets.
- PostgreSQL/Redis, worker, audit persistence, migration application, backup/restore, staging, rollback, container builds and scans require infrastructure not present on this workstation. Offline migration SQL and unit contracts pass, but they are not substitutes for those tests.
- Existing ingestion/evaluation endpoints retain synchronous development behavior. Production clients should submit persisted IDs/object references through `POST /api/jobs`; moving every existing frontend workflow to asynchronous polling is still required before enabling large production inputs.
- Automated retention currently removes only traces carrying explicit expiry. Audit/evaluation/feedback/job cleanup remains disabled until legal-hold-aware fields and review are implemented.
- Mypy checks all 210 modules but has an explicit legacy-error baseline for 11 older analytics/decision/ingestion module patterns in `pyproject.toml`; remove that baseline incrementally.
- `npm audit` reports two moderate PostCSS findings inherited by the current latest Next.js 16.2.10. The offered forced fix downgrades Next to 9.3.3 and is unsafe; monitor the upstream patched release and keep CSP/output encoding controls active.
- Audit rows are append-only through the API/service and runtime SQL template, but a privileged database administrator can still alter them. Export to immutable external audit storage where regulatory non-repudiation is required.
- Compose examples define baseline isolation/hardening, not measured CPU/memory limits; set target-platform quotas from staging load tests.
