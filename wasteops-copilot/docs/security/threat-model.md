# WasteOps threat model

This living model uses STRIDE to prioritize controls; it does not eliminate risk.

## Assets and actors

Assets include operational records, workforce data, knowledge documents, prompt versions, audit/evaluation history, credentials, backups, model access, and decision recommendations. Actors are authorized operators/admins/auditors, identity and cloud providers, external attackers, malicious insiders, and compromised dependencies.

## Trust boundaries and entry points

Boundaries exist between browser and TLS proxy, proxy and frontend/backend, API and OIDC/JWKS, API/worker and PostgreSQL/Redis, providers, object storage, CI runners, and backup storage. Entry points are OIDC callbacks, BFF/API routes, document/CSV ingestion, model inputs/outputs, administrative endpoints, queue messages, deployment pipelines, and restore tooling.

| STRIDE | Threat | Controls | Residual risk |
|---|---|---|---|
| Spoofing | Stolen/forged access token, provider compromise | OIDC signature/issuer/audience/time/algorithm validation, TLS, short lifetime, key rotation, HTTP-only encrypted session | A valid stolen token works until expiry/revocation policy takes effect. |
| Tampering | Unauthorized prompt activation, CSV/document manipulation, backup modification | Granular RBAC, immutable versions/audit, file hashes, schema validation, encrypted backups and checksums, human approval | Privileged insiders and compromised admins remain material risks. |
| Repudiation | Admin denies ingestion or configuration change | Append-only minimized audit records, request IDs, protected audit reads | Database administrators can alter storage; external immutable export is recommended. |
| Information disclosure | Secret/trace/prompt/SQL/embedding leak, backup theft | Scrubbing, safe schemas, private storage, encryption, least-privilege DB roles, no public DB/Redis, CSP | Provider-side retention and operator screenshots require policy controls. |
| Denial of service | Expensive AI requests, ingestion bombs, queue flood | Body limits, Redis rate limits, proxy timeouts, worker concurrency, health checks, resource quotas | Coordinated distributed attacks may require upstream WAF/capacity controls. |
| Elevation | Role claim abuse, IDOR, open proxy/path traversal | Backend permissions, strict claim shapes, BFF allow-list, hashed resource audit, path-safe storage | Incorrect IdP group assignment can grant legitimate but excessive access. |

Prompt injection and malicious documents are untrusted data, never instructions: retrieval is bounded, outputs cannot execute SQL or operations, model HTML is not rendered, citations are validated, and decisions always require humans. SQL is parameterized/allow-listed. Supply-chain controls include dependency/secret/static/container scans, SBOMs, immutable image tags, and pinned sensitive scanning actions. Provider outages fail closed rather than enabling development auth or fabricating answers.

Review this model for each new provider, route, data class, deployment architecture, and security incident.
