# Local Development Runbook

## Setup

```bash
cp .env.example .env
make bootstrap
make migrate
```

`make bootstrap` recreates `.venv` with `python -m venv` and installs dev dependencies via `pip`.

## Start API

```bash
make dev
```

## Basic smoke test

```bash
curl http://127.0.0.1:8000/healthz
```

## Trigger sync

```bash
curl -X POST http://127.0.0.1:8000/v1/sync/redmine -H 'content-type: application/json' -d '{}'
```

Or from CLI:

```bash
make sync
```

Sync behavior:
- runs deterministic module order (`projects` -> `wiki`)
- persists raw and normalized rows with idempotent upserts
- updates incremental cursors for entities with `updated_on` filtering (`issues`, `time_entries`)
- records global lifecycle in `sync_state` and per-entity cursor state in `sync_cursor`
- incrementally refreshes `doc_chunk` sources and SQLite FTS index for lexical retrieval

## Full chunk reindex

```bash
make reindex
```

## Refresh embeddings only

```bash
make embed
```

For full vector rebuild:

```bash
.venv/bin/python -m redmine_rag.cli index embeddings --full-rebuild
```

## Run deterministic extraction

```bash
.venv/bin/python -m redmine_rag.cli extract run
```

Enable LLM structured extraction (optional):

```bash
export LLM_PROVIDER=mock
export LLM_EXTRACT_ENABLED=true
export LLM_EXTRACT_MAX_RETRIES=2
export LLM_EXTRACT_TIMEOUT_S=20
export LLM_EXTRACT_COST_LIMIT_USD=1.0
```

For local development the default provider `mock` is deterministic and offline.

Or via API:

```bash
curl -X POST http://127.0.0.1:8000/v1/extract/properties \
  -H 'content-type: application/json' \
  -d '{}'
```

Notes on extraction limits:
- `LLM_EXTRACT_TIMEOUT_S` bounds per-issue latency budget.
- `LLM_EXTRACT_COST_LIMIT_USD` limits total estimated extraction spend per run.
- `LLM_EXTRACT_MAX_CONTEXT_CHARS` caps issue context size to keep prompts bounded.

## Query workflow metrics summary

```bash
curl "http://127.0.0.1:8000/v1/metrics/summary?project_ids=1&from_date=2026-02-01T00:00:00Z&to_date=2026-02-21T23:59:59Z"
```

## Run eval regression gate

```bash
make eval-gate
```

For live eval run against local API:

```bash
python3 scripts/eval/run_eval.py --api-base-url http://127.0.0.1:8000 --output-results evals/results.latest.jsonl
```

## Develop without real Redmine access

```bash
make mock-redmine
```

Set `.env` to local mock values (see `docs/runbooks/mock-redmine.md`).
