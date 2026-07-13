# WasteOps Decision Intelligence Copilot

WasteOps is a production-oriented FastAPI foundation for hybrid retrieval-augmented decision support in waste-management operations. It combines exact PostgreSQL queries over operational datasets with pgvector search over procedures, manuals, policies, and incident documents. Responses expose evidence, uncertainty, alternatives, risks, and an application-calculated confidence score.

## Architecture

```text
Manager/API client
      |
   FastAPI
      |
 Intent router -- LLM JSON classification, deterministic fallback
      |
      +-- SQL retriever -- validated SELECT/WITH only -- PostgreSQL
      +-- Vector retriever -- embeddings/cosine search -- pgvector
      |
 Hybrid evidence -> grounded LLM services -> typed response
```

SQL performs numerical aggregation rather than asking the model to calculate over text. Generated SQL is accepted only after validation, has a row limit, runs with `statement_timeout`, and should use a database role granted `SELECT` only in production. Document chunks retain source and operational metadata for citations.

## Project layout

- `app/api`: typed HTTP endpoints and dependency composition
- `app/core`: environment configuration, database, logging, and SQL safety
- `app/models`: SQLAlchemy operational and pgvector models
- `app/ingestion`: validated CSV and document ingestion
- `app/retrieval`: intent, SQL, vector, and hybrid retrieval
- `app/services`: LLM, RAG, decision, incident, and report services
- `app/prompts`: version-controlled safety and grounding prompts
- `data/raw`: unchanged source CSVs
- `data/documents`: PDF, TXT, Markdown, and DOCX knowledge files
- `migrations`: Alembic database revisions
- `scripts`: database and ingestion entry points
- `tests`: unit/API smoke tests

## Local installation

Python 3.12 and PostgreSQL 16 with pgvector are required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Edit `.env`; never commit an API key. Start the API with:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for OpenAPI documentation. `GET /api/health` is a liveness endpoint and intentionally does not fail when PostgreSQL or the model provider is unavailable.

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Compose starts PostgreSQL/pgvector, waits for database health, applies migrations, and starts the API on port 8000. For production, replace the example credentials, terminate TLS at an ingress, store secrets outside `.env`, and use a restricted runtime database user with only `CONNECT`, `USAGE`, and `SELECT` for retrieval. Use a separate migration/ingestion role for writes.

## Environment variables

| Variable | Purpose | Example/default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy async PostgreSQL URL | `postgresql+asyncpg://...` |
| `LLM_API_KEY` | OpenAI-compatible provider secret | empty |
| `LLM_BASE_URL` | Compatible API root | `https://api.openai.com/v1` |
| `CHAT_MODEL_NAME` | Chat model | `gpt-4.1-mini` |
| `EMBEDDING_MODEL_NAME` | Embedding model | `text-embedding-3-small` |
| `VECTOR_DIMENSIONS` | Vector column/API dimensions | `1536` |
| `RETRIEVAL_TOP_K` | Semantic result count | `8` |
| `APP_ENVIRONMENT` | Runtime label | `development` |
| `LOG_LEVEL` | Structured log threshold | `INFO` |
| `SQL_QUERY_TIMEOUT_MS` | Database statement timeout | `5000` |
| `SQL_ROW_LIMIT` | Maximum generated-query rows | `200` |
| `DATA_DIR` | Data directory | `data` |

Changing vector dimensions after migration requires a schema migration and re-embedding documents.

## Database and ingestion

Apply or roll back migrations:

```powershell
alembic upgrade head
alembic downgrade -1
```

The eight original CSVs are copied unchanged to `data/raw`. The loader normalizes headings in memory, validates columns, converts dates/timestamps, maps missing values to SQL `NULL`, reports failed row numbers, and uses natural/composite uniqueness constraints to skip duplicates.

```powershell
python scripts/ingest_csv_data.py
curl.exe -X POST http://localhost:8000/api/ingestion/csv -H "Content-Type: application/json" -d '{"filenames":null}'
```

Place supported knowledge files in `data/documents`, then ingest them:

```powershell
python scripts/ingest_documents.py --department Operations --asset-type smart-bin --region "Greater Cairo" --version 1.0
curl.exe -X POST http://localhost:8000/api/ingestion/documents -H "Content-Type: application/json" -d '{"department":"Operations","region":"Greater Cairo"}'
```

Optional document metadata consists of department, asset type, region, effective date (`YYYY-MM-DD`), and version. Filename, type, content hash, and chunk number are always stored.

## API examples

```powershell
curl.exe -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"question":"Which bins require immediate attention?"}'
curl.exe -X POST http://localhost:8000/api/decisions/recommend -H "Content-Type: application/json" -d '{"question":"What is the best collection plan for tomorrow?"}'
curl.exe -X POST http://localhost:8000/api/incidents/investigate -H "Content-Type: application/json" -d '{"question":"Why were collections missed in Greater Cairo?"}'
```

## Testing

```powershell
pytest
ruff check app tests scripts
```

Tests cover liveness, offline intent routing, dataset mappings, SQL rejection/limits, and deterministic confidence scoring. Integration tests against a disposable pgvector database and a stub OpenAI-compatible provider should be added in CI.

## Current limitations

- No frontend, authentication/authorization, background job queue, reranker, or streaming response yet.
- Document ingestion is synchronous from the caller's perspective and OCR is not included for scanned PDFs.
- The initial generated-SQL guard is deliberately conservative; a SQL AST validator and database proxy policy are recommended before broad production access.
- The fallback intent router extracts asset identifiers but not free-form region/date entities.
- Source agreement in confidence scoring begins as source-type diversity; domain-specific contradiction detection should replace it after evaluation data exists.
- Operational CSV identifiers contain the source encoding exactly as received; no destructive text repair is attempted.

## Future prediction API integration

`PredictionGateway` defines the boundary for future Data Science services: `predict_bin_overflow`, `calculate_collection_priority`, `detect_truck_anomaly`, `predict_missed_collection`, and `forecast_workforce_requirement`. Implement it as a separately tested HTTP client, attach model/version metadata to evidence, and keep predictive outputs distinct from observed database facts. No prediction model is included in this foundation.
