# WasteOps ML Service

Private FastAPI model serving and governed training for overflow risk, collection priority, truck anomalies, missed-collection risk, and workforce requirements.

Predictions are advisory, not guaranteed outcomes. They never dispatch trucks, assign workers, change asset status, or make disciplinary decisions. Probability is distinct from Decision Intelligence confidence, and every operational recommendation requires human approval.

## Local checks

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy
uvicorn app.main:app --port 8001
```

Service endpoints require a bearer `SERVICE_TOKEN`; model and monitoring detail requires `ADMIN_SERVICE_TOKEN`. Production additionally requires a read-only analytics URL and a model checksum allow-list.

Training accepts reviewed point-in-time feature datasets. It does not silently convert raw operational files into production candidates. Promotion is explicit:

```bash
python scripts/promote_model.py --model bin-overflow --version 3 --stage Production --approved-by USER-ID
```
