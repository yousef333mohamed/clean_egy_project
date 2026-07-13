# Production configuration

Start from `.env.production.example`, replacing placeholders through Docker/Kubernetes/cloud secrets. Never commit the resulting environment file. `_FILE` is supported for database URLs, Redis URL, LLM key, and metrics token.

Production validation requires OIDC/JWKS HTTPS URLs, authentication, human approval, explicit HTTPS CORS, no localhost, development auth off, and all debug APIs off. Configure trusted public hosts, release metadata, private storage, Redis-required rate limiting, retention, and provider timeouts.

Only `NEXT_PUBLIC_*` values are browser-visible and none may contain credentials. `AUTH_SECRET`, OIDC client secret, internal backend URL, provider keys, and storage/database values are server-only.

The scheduled cleanup currently deletes only traces whose explicit expiry elapsed. Audit, evaluation, feedback, and failed-job deletion must remain disabled until the target deployment adds legal-hold-aware persistence for those record types.
