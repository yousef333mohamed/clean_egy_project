# ML limitations

- No approved production model or genuine model metrics are included in source control. Baselines are code paths, not evidence that production quality gates passed.
- Sample CSVs are insufficient to establish prospective accuracy, calibration, seasonal stability, or operational subgroup fairness.
- Missed-collection and workforce features currently have incomplete cross-domain availability; the service warns or rejects data-deficient scope.
- Environmental, traffic, holiday, festival, and complaint timing need governed availability contracts before candidate use.
- Drift thresholds are initial review thresholds and require empirical tuning.
- Backfill execution is intentionally blocked until a resumable historical as-of feature store is configured.
- Prediction persistence tables exist, but durable writing should be enabled only with retention, legal, and access controls in the target environment.
- MLflow and Docker deployment were authored but require external PostgreSQL, object storage, secrets, approved artifacts, and staging validation.

Predictions are not guaranteed outcomes; historical backtests do not guarantee future results. Humans remain responsible for operational approval. Workforce forecasts cannot support disciplinary decisions.
