# Go-live checklist

- [ ] Production domains configured and TLS active/renewal tested
- [ ] OIDC configured; development authentication disabled; RBAC tested
- [ ] CORS restricted; CSP and security headers active; rate limiting active
- [ ] Secrets securely stored/rotatable; database roles restricted
- [ ] Backups configured and restore tested
- [ ] Monitoring active and alerts tested
- [ ] Migrations applied once and revision recorded
- [ ] Quality gates and safety suite passed
- [ ] Administrative APIs protected and debug APIs disabled
- [ ] Database/Redis/backend are not public
- [ ] Smoke tests and production-mode provider outage tests passed
- [ ] Rollback tested with the preserved immutable version
