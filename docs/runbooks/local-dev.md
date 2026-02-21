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

## Start frontend console (Task 16+)

```bash
make ui-install
make ui-dev
```

Open `http://127.0.0.1:5173`.

Sync control center workflow (Task 17):
- open `Sync` page
- set project scope + module toggles
- trigger sync and monitor live table updates
- select a failed job and use `Retry selected job`

Ops hardening workflow (Task 20):
- open `Ops` page
- validate environment cards (`app env`, `LLM provider/model`, health snapshot)
- run `Run backup` and check `Operations Run History`
- run `Run maintenance` and verify completion feedback
- complete `Release Readiness Checklist` before cutover rehearsal

Backend-served SPA mode:

```bash
make ui-build
make dev
```

Then open `http://127.0.0.1:8000/app`.

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

Inspect sync job status:

```bash
curl "http://127.0.0.1:8000/v1/sync/jobs?limit=20"
curl "http://127.0.0.1:8000/v1/sync/jobs/<job_id>"
```

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

Use local Ollama runtime instead of mock:

```bash
ollama pull Mistral-7B-Instruct-v0.3-Q4_K_M
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=Mistral-7B-Instruct-v0.3-Q4_K_M
export OLLAMA_TIMEOUT_S=45
export OLLAMA_MAX_CONCURRENCY=2
export ASK_ANSWER_MODE=llm_grounded
export ASK_LLM_MAX_RETRIES=1
export ASK_LLM_COST_LIMIT_USD=0.05
export LLM_RUNTIME_COST_LIMIT_USD=10.0
export LLM_CIRCUIT_BREAKER_ENABLED=true
export LLM_CIRCUIT_FAILURE_THRESHOLD=3
export LLM_CIRCUIT_SLOW_THRESHOLD_MS=15000
export LLM_CIRCUIT_SLOW_THRESHOLD_HITS=3
export LLM_CIRCUIT_OPEN_SECONDS=60
export LLM_SLO_MIN_SUCCESS_RATE=0.9
export LLM_SLO_P95_LATENCY_MS=12000
export RETRIEVAL_PLANNER_ENABLED=true
export RETRIEVAL_PLANNER_MAX_EXPANSIONS=3
export RETRIEVAL_PLANNER_TIMEOUT_S=12
```

Runtime readiness is visible in:

```bash
curl http://127.0.0.1:8000/healthz
```

Ask endpoint with grounded LLM synthesis:

```bash
curl -X POST http://127.0.0.1:8000/v1/ask \
  -H 'content-type: application/json' \
  -d '{"query":"What is the login callback issue and rollback plan?","filters":{"project_ids":[1]},"top_k":5}'
```

Planner notes:
- planner output includes `normalized_query`, bounded `expansions`, and optional filter hints.
- planner-suggested IDs are applied only if they exist in local DB domain tables.
- if planner fails or returns invalid payload, retrieval falls back to original user query.
- guardrail rejections are tracked by buckets in `/healthz` under `guardrails`.
- LLM runtime telemetry is available in `/healthz` under `llm_telemetry` (JSON payload in `detail`).

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
- `LLM_RUNTIME_COST_LIMIT_USD` applies a global runtime budget across ask/extract LLM calls.
- circuit-breaker fallback can temporarily force deterministic mode when repeated failures/slow calls occur.

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

With LLM reliability/latency gate:

```bash
python3 scripts/eval/check_regression_gate.py \
  --current evals/reports/latest_eval_report.json \
  --baseline evals/baseline_metrics.v1.json \
  --max-llm-error-rate 0.15 \
  --max-llm-p95-latency-ms 20000 \
  --require-llm-circuit-closed
```

## Ops commands

```bash
.venv/bin/python -m redmine_rag.cli ops backup --output-dir backups
.venv/bin/python -m redmine_rag.cli ops maintenance
```

Recovery and incident procedures are in `docs/runbooks/operations.md`.

## Develop without real Redmine access

```bash
make mock-redmine
```

Set `.env` to local mock values (see `docs/runbooks/mock-redmine.md`).
