# Promotion process

Promotion is an explicit human-controlled command:

```bash
python scripts/promote_model.py --model bin-overflow --version 3 --stage Production --approved-by USER-ID
```

The gate requires validation, leakage checks, baseline improvement, calibration review, no critical subgroup failure, approved metadata, and an existing model card. The dashboard can request review but cannot promote. The ML model, an LLM, a single metric, CI, retraining, or the frontend cannot approve promotion.

Rollback promotes a previously approved compatible version after checksum and quality verification, then confirms readiness, contract tests, and prediction distribution.
