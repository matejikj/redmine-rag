# Release Cutover Checklist (UI + API)

Use this checklist for go-live dry runs and release sign-off.

## 1. Build and startup verification

1. Run backend checks: `make check`.
2. Build frontend bundle: `make ui-build`.
3. Start API: `make dev`.
4. Open `http://127.0.0.1:8000/app` and verify UI loads.

## 2. Core user journey verification

1. `Sync` page:
   - trigger scoped sync job
   - confirm queued/running/finished transitions
2. `Ask` page:
   - run query with project filter
   - inspect citations and claim mapping
3. `Metrics` page:
   - apply deterministic date/project filters
   - run extraction and verify counters
   - review eval/regression status widget
4. `Ops` page:
   - verify runtime environment fields
   - run backup action and confirm history row
   - run maintenance action and confirm history row

## 3. API contract verification

1. `GET /healthz`
2. `POST /v1/sync/redmine`
3. `GET /v1/sync/jobs`
4. `POST /v1/ask`
5. `POST /v1/extract/properties`
6. `GET /v1/metrics/summary`
7. `GET /v1/evals/latest`
8. `GET /v1/ops/environment`
9. `GET /v1/ops/runs`
10. `POST /v1/ops/backup`
11. `POST /v1/ops/maintenance`

## 4. Rollback rehearsal

1. Trigger backup from `Ops` page.
2. Validate snapshot manifest exists in backup directory.
3. Perform restore rehearsal in non-production environment using:
   - `.venv/bin/python -m redmine_rag.cli ops restore --source-dir <snapshot-dir> --force`
4. Re-run health and ask smoke checks.

## 5. Exit criteria

1. No blocking errors in health checks.
2. Regression gate status reviewed and accepted.
3. Backup + maintenance run entries recorded successfully.
4. UAT sign-off captured with timestamp and operator names.
