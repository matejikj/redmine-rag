# Task 17: UI Sync and Ingestion Control Center

## Goal

Provide intuitive UI controls for sync operations, job tracking, and ingestion diagnostics.

## Scope

- Add sync trigger form (project scope, module toggles).
- Add live job list/detail view with status filters.
- Show ingestion summaries (entities/chunks/vectors) per job.
- Surface failed job diagnostics and recommended next actions.

## Deliverables

- Sync operations page connected to `/v1/sync/redmine` and sync job endpoints.
- Job detail panel with payload summary and timestamps.
- Visual states for queued/running/finished/failed jobs.
- Retry and refresh actions in UI.

## Acceptance Criteria

- User can start sync and monitor progress without CLI usage.
- Failed jobs are easy to identify and inspect.
- Key job metrics are readable and comparable across runs.
- UI behavior remains stable across page refreshes.

## Quality Gates

- E2E tests for trigger + monitor flow.
- API contract tests for job list/detail rendering.
- UX review focused on operator workflow speed and clarity.
