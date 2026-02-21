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

## Develop without real Redmine access

```bash
make mock-redmine
```

Set `.env` to local mock values (see `docs/runbooks/mock-redmine.md`).
