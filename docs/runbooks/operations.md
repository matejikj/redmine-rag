# Operations Runbook

## Scope

This runbook covers production hardening tasks for sync health, incident response, backup/recovery, and runtime tuning.

## Health and Observability

- `GET /healthz` now includes:
  - DB probe status and latency
  - sync job counters (`queued`, `running`, `finished`, `failed`)
  - config/security checks (`outbound_policy`, `secrets`)
  - LLM runtime check (`llm_runtime`) including Ollama reachability/model readiness
  - guardrail counters (`guardrails`) across buckets:
    - `prompt_injection`
    - `ungrounded_claim`
    - `schema_violation`
    - `unsafe_content`
- Sync job visibility:
  - `POST /v1/sync/redmine` creates a traceable job ID
  - `GET /v1/sync/jobs/{job_id}` returns lifecycle and error details
  - `GET /v1/sync/jobs?limit=20&status=failed` supports operational triage
- Logs are structured JSON; automation can filter by fields like `job_id`, `project_ids`, `retrieval_mode`, `extractor_version`.

## Incident Response

1. Confirm API health:
   - `curl http://127.0.0.1:8000/healthz`
2. Inspect recent failing sync jobs:
   - `curl "http://127.0.0.1:8000/v1/sync/jobs?status=failed&limit=20"`
3. For specific job:
   - `curl "http://127.0.0.1:8000/v1/sync/jobs/<job_id>"`
4. If Redmine network issues are present:
   - verify `REDMINE_BASE_URL`, SSL, and allowlist (`REDMINE_ALLOWED_HOSTS`)
   - retry with targeted sync scope (`project_ids`)

## Backup and Recovery

### Create backup

```bash
.venv/bin/python -m redmine_rag.cli ops backup --output-dir backups
```

Snapshot includes:
- SQLite DB file
- vector index (`chunks.index`)
- vector metadata (`chunks.meta.json`)
- `manifest.json`

### Restore backup

```bash
.venv/bin/python -m redmine_rag.cli ops restore --source-dir backups/snapshot-<timestamp> --force
```

`--force` is required to avoid accidental overwrite.

### Maintenance

```bash
.venv/bin/python -m redmine_rag.cli ops maintenance
```

Runs:
- WAL checkpoint truncate
- `VACUUM`
- `ANALYZE`

## Failure Modes and Actions

- `database` check = `fail`:
  - restore latest backup
  - run maintenance
  - re-run incremental sync
- high `failed` sync job count:
  - inspect most recent failed jobs
  - validate Redmine connectivity and credentials
  - re-run sync after remediation
- degraded security checks in production:
  - rotate `REDMINE_API_KEY`
  - enforce `REDMINE_ALLOWED_HOSTS`
- degraded `llm_runtime` with `LLM_PROVIDER=ollama`:
  - verify Ollama server is running and reachable
  - verify `OLLAMA_MODEL` exists in `ollama list`
  - re-run extraction after runtime recovery
- non-zero `guardrails` counters:
  - inspect logs for `guardrail_reason` and `guardrail_context`
  - confirm blocked content is expected (red-team test) or malicious input attempt
  - if false positives grow, tune guardrail patterns and rerun regression tests

## Soak Test (Medium Dataset)

```bash
python3 scripts/ops/soak_sync.py --iterations 3 --project-id 1
```

Use this before release candidates to verify repeated incremental sync stability.

## Runtime Tuning Profiles

### M1 / Laptop

- `EMBEDDING_DIM=256`
- `RETRIEVAL_CANDIDATE_MULTIPLIER=4`
- `LLM_EXTRACT_BATCH_SIZE=20`
- `REDMINE_HTTP_TIMEOUT_S=30`
- `OLLAMA_TIMEOUT_S=45`
- `OLLAMA_MAX_CONCURRENCY=2`

### Server

- increase concurrency externally (multiple workers/processes)
- consider higher `RETRIEVAL_CANDIDATE_MULTIPLIER` after profiling
- tighten outbound policy:
  - `REDMINE_ALLOWED_HOSTS=<trusted-hosts>`
  - enforce HTTPS Redmine endpoint

## Security Checklist

- `REDMINE_API_KEY` is not placeholder in production.
- `REDMINE_ALLOWED_HOSTS` is explicitly configured in production.
- Redmine endpoint uses HTTPS (except localhost development).
- No secrets are logged in plaintext.
- Input payload IDs are positive and bounded by schema limits.
