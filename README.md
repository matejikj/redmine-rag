# redmine-rag

Agent-first platform for retrieving Redmine knowledge (issues, journals, wiki), generating grounded answers, and attaching source citations.

## Goals

- Ingest Redmine data incrementally (`updated_on` based sync).
- Persist both raw payloads and normalized entities with idempotent upserts.
- Build hybrid retrieval (FTS + vector similarity).
- Generate answers grounded in retrieved chunks.
- Enforce citations per claim and keep full auditability.

## Tech Stack (optimized for MacBook Air M1, 16 GB)

- API: FastAPI
- Storage: SQLite (WAL) + FTS5
- Vectors: local index abstraction (`numpy` baseline, pluggable backend)
- Migrations: Alembic
- Worker: lightweight async scheduler/CLI jobs
- Tooling: `venv`, `pip`, `ruff`, `mypy`, `pytest`, `pre-commit`

## Quick start

```bash
cp .env.example .env
make bootstrap
make migrate
make dev
```

`make bootstrap` creates `.venv`, installs dependencies with `pip`, and sets git hooks.

Open `http://127.0.0.1:8000/docs`.

## Docker (optional)

```bash
docker compose up --build
```

## Common commands

```bash
make format
make lint
make typecheck
make test
make check
make sync
make reindex
make embed
make eval
make eval-baseline
make eval-gate
make dataset-quality
make mock-redmine
.venv/bin/python -m redmine_rag.cli ops backup --output-dir backups
.venv/bin/python -m redmine_rag.cli ops maintenance
```

## Project layout

- `src/redmine_rag/` application code
- `migrations/` Alembic migration scripts
- `tests/` test suite
- `docs/` architecture and runbooks
- `docs/runbooks/operations.md` production operations, backup/recovery, and incident response
- `docs/data-model.md` normalized and raw data model reference
- `prompts/` reusable prompt assets
- `evals/` evaluation datasets
- `scripts/` bootstrap and CI scripts

## API contracts (initial)

- `GET /healthz`
- `POST /v1/ask`
- `POST /v1/sync/redmine`
- `GET /v1/sync/jobs`
- `GET /v1/sync/jobs/{job_id}`
- `POST /v1/extract/properties`
- `GET /v1/metrics/summary`

`POST /v1/ask` behavior:
- returns only grounded claims derived from retrieved chunks
- enforces citation marker per claim (`[1]`, `[2]`, ...)
- returns explicit "not enough evidence" fallback when grounding is insufficient

Deterministic extraction:
- `POST /v1/extract/properties` computes `issue_metric` + `issue_property` with extractor version `det-v1`.
- Formula `first_response_s`: seconds between `issue.created_on` and first journal event at/after creation.
- Formula `resolution_s`: seconds between `issue.created_on` and first transition to a closed status (`issue_status.is_closed=true`), fallback `issue.closed_on`.
- `reopen_count`: transitions into `Reopened` (or closed -> non-closed fallback).
- `touch_count`: number of journal records on the issue.
- `handoff_count`: number of `assigned_to_id` transitions where old/new assignee are both set and differ.
- Validation markers in `issue_property.props_json.validation`: timestamp anomalies, status chain breaks, missing status values, unknown status IDs.

LLM structured extraction (JSON Schema):
- Enabled by `LLM_EXTRACT_ENABLED=true` and runs inside `POST /v1/extract/properties`.
- Prompt and schema are versioned in repo:
  - `prompts/extract_properties_v1.md`
  - `prompts/extract_properties_schema_v1.json`
- Extraction output is stored under `issue_property.props_json.llm` with:
  - `extractor_version` (`llm-json-v1`)
  - `prompt_version`
  - `schema_version`
  - `attempts`, `error_bucket`, `latency_ms`, `estimated_cost_usd`
  - validated `properties` payload
- Retry behavior:
  - invalid JSON and schema violations are retried up to `LLM_EXTRACT_MAX_RETRIES`
  - failed issues are bucketed (`invalid_json`, `schema_validation`, `timeout`, `provider_error`)
- Version strategy:
  - deterministic-only rows keep `extractor_version=det-v1`
  - deterministic + LLM rows store `extractor_version=det-v1+llm-json-v1`

Metrics summary endpoint:
- `GET /v1/metrics/summary?project_ids=1&project_ids=2&from_date=2026-02-01T00:00:00Z&to_date=2026-02-21T23:59:59Z`
- Returns global aggregates and `by_project` breakdown for issues extracted by `det-v1`.

## Mock Redmine API

For local development without real Redmine access:

```bash
make mock-redmine
```

Then set:

```bash
REDMINE_BASE_URL=http://127.0.0.1:8081
REDMINE_API_KEY=mock-api-key
```

See `docs/runbooks/mock-redmine.md` for details.

## Ingestion module configuration

You can enable/disable ingestion modules via `.env`:

```bash
REDMINE_MODULES=projects,users,groups,trackers,issue_statuses,issue_priorities,issues,time_entries,news,documents,files,boards,wiki
REDMINE_BOARD_IDS=94001,94003
REDMINE_WIKI_PAGES=platform-core:Feature-Login,platform-core:Incident-Triage-Playbook
EMBEDDING_DIM=256
RETRIEVAL_LEXICAL_WEIGHT=0.65
RETRIEVAL_VECTOR_WEIGHT=0.35
RETRIEVAL_RRF_K=60
RETRIEVAL_CANDIDATE_MULTIPLIER=4
```

- `REDMINE_MODULES`: registry toggle for sync pipeline modules.
- `REDMINE_BOARD_IDS`: board IDs for board/message ingestion.
- `REDMINE_WIKI_PAGES`: wiki references in `project_ref:title` format.
- `EMBEDDING_DIM`: local deterministic embedding dimension.
- `RETRIEVAL_*`: hybrid fusion parameters (weights, RRF constant, candidate multiplier).

## Chunking and FTS

- Incremental sync updates `doc_chunk` for issues, journals, wiki pages, attachments, time entries, news, documents, and board messages.
- SQLite FTS5 index is maintained by triggers on `doc_chunk`.
- For full rebuild of chunks and FTS content, run:

```bash
make reindex
```

## Agent-first development

Read `AGENTS.md` and `docs/agent-workflow.md` before implementing features.
