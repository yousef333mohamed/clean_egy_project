# Security checklist

- [ ] OIDC keys/issuer/audience/expiry and every role tested; development auth off.
- [ ] Administrative, ingestion, traces, audit, prompts, jobs, and metrics access tested.
- [ ] Exact CORS/trusted hosts, CSRF origin checks, nonce CSP, HSTS/TLS, limits and timeouts active.
- [ ] Runtime/migration/analytics/backup DB roles separated; DB and Redis private.
- [ ] Secrets injected, rotation owners defined, logs/traces/error monitor redaction sampled.
- [ ] Dependencies, SAST, secrets, images, configuration and SBOM gates clean.
- [ ] Encrypted backup restored successfully; object storage private and versioned.
- [ ] Alerts, outage degradation, incident response, rollback, and human decision approval tested.
