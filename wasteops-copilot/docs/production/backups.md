# Backups

Run scheduled custom-format PostgreSQL dumps as `wasteops_backup`, encrypt with an approved `age` recipient, transfer over encrypted transport to immutable private storage, retain 30 days unless policy requires more, and alert on failure. Database dumps include prompt versions, document metadata, evaluations, feedback, and audit. Back up original documents/uploads separately with versioning and retention.

At least monthly, restore to an isolated non-production database with `restore.sh`, apply checksum/decryption verification, check Alembic revision and critical table counts, then run smoke/evaluation integrity tests. Record duration, revision, artifact hash, reviewer, and destruction of the restored environment. A backup is not successful operational evidence until restore verification passes.
