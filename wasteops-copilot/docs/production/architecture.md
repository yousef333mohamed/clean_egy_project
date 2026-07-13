# Production architecture

Internet traffic reaches only Nginx over TLS. Nginx routes pages and Auth.js callbacks to Next.js and `/api` to FastAPI. Auth.js holds OIDC tokens in an encrypted HTTP-only cookie; its allow-listed BFF sends the access token as Bearer credentials. FastAPI validates it independently and authorizes every domain route.

FastAPI, Celery workers, PostgreSQL, and authenticated Redis occupy a private network. Workers accept only IDs/object references. PostgreSQL is authoritative for audit, prompt, evaluation, ingestion, and operational data; Redis is disposable coordination/rate-limit state. Private encrypted S3-compatible storage holds original files and reports. Metrics and logs flow to protected monitoring systems.

Migrations are a single reviewed release job using the migration role. Runtime, analytics, backup, and migration identities have separate grants.
