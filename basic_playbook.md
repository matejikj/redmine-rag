# Basic End-to-End Playbook (Mock Redmine)

This guide shows the fastest way to run the app end-to-end with the local mock Redmine server and verify the full project build/check flow.

## 1. Prerequisites

- Python `3.12+`
- `make`
- `git`

## 2. Initial setup

```bash
cp .env.example .env
```

Update `.env` for local mock usage:

```env
REDMINE_BASE_URL=http://127.0.0.1:8081
REDMINE_API_KEY=mock-api-key
REDMINE_ALLOWED_HOSTS=127.0.0.1,localhost
REDMINE_PROJECT_IDS=1
```

Install dependencies and create local DB schema:

```bash
make bootstrap
make migrate
```

## 3. Start mock Redmine (Terminal A)

```bash
MOCK_REDMINE_DATASET_PROFILE=small make mock-redmine
```

Quick check:

```bash
curl http://127.0.0.1:8081/projects.json -H "X-Redmine-API-Key: mock-api-key"
```

## 4. Start API (Terminal B)

```bash
make dev
```

Health check:

```bash
curl http://127.0.0.1:8000/healthz
```

## 5. Run basic E2E flow (Terminal C)

Trigger sync:

```bash
curl -X POST http://127.0.0.1:8000/v1/sync/redmine \
  -H "content-type: application/json" \
  -d '{"project_ids":[1]}'
```

Inspect sync jobs:

```bash
curl "http://127.0.0.1:8000/v1/sync/jobs?limit=20"
```

Run property extraction:

```bash
curl -X POST http://127.0.0.1:8000/v1/extract/properties \
  -H "content-type: application/json" \
  -d '{"issue_ids":[1001,1002]}'
```

Ask grounded question:

```bash
curl -X POST http://127.0.0.1:8000/v1/ask \
  -H "content-type: application/json" \
  -d '{"query":"What is the login callback problem and rollback plan?","filters":{"project_ids":[1]},"top_k":5}'
```

Read metrics summary:

```bash
curl "http://127.0.0.1:8000/v1/metrics/summary?project_ids=1"
```

## 6. Build and verify the whole app

Run formatting, static checks, and tests:

```bash
make format
make check
```

Optional regression gate:

```bash
make eval-gate
```

## 7. Optional ops checks

```bash
.venv/bin/python -m redmine_rag.cli ops backup --output-dir backups
.venv/bin/python -m redmine_rag.cli ops maintenance
```

## 8. Stop services

- Stop `make dev` with `Ctrl+C`
- Stop `make mock-redmine` with `Ctrl+C`
