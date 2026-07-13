# Release process

Use semantic release versions plus commit SHA and build timestamp. CI quality/security workflows must pass; produced images and SBOMs are immutable. Staging deploys the same image digests, runs one migration, smoke tests, a small deterministic evaluation/safety suite, and rollback practice.

Production uses a protected environment with manual approval, confirmed backup/quality gates, recorded old tag and Alembic revision, migration, rolling deployment, smoke tests, and monitoring verification. Roll back application images with `rollback.sh`; never automatically downgrade the database. Review and document any forward-fix or restore decision.
