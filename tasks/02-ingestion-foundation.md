# Task 02: Ingestion Foundation (Raw + Normalized)

## Goal

Implement robust ingestion from Redmine API into raw and normalized storage for all relevant Redmine entities.

## Scope

- Read all enabled Redmine entities from API:
  - Issues and linked data (`journals/comments`, attachments, relations, watchers, custom fields)
  - Wiki pages + versions
  - Time entries
  - Projects, trackers, statuses, priorities, categories, versions
  - Users, groups, memberships
  - News, documents/files, boards/messages (if enabled)
- Save full payloads to raw tables.
- Normalize core entities into relational tables.
- Add idempotent upsert logic.

## Deliverables

- Ingestion pipeline with clear service boundaries.
- Upsert repository layer for normalized entities and `raw_*`.
- Entity registry/config that enables or disables ingestion per Redmine module.
- Sync state tracking (`last_sync_at`, error handling).

## Acceptance Criteria

- Re-running sync does not duplicate data.
- Changed records are updated correctly.
- Unsupported or disabled Redmine modules are skipped gracefully with clear logs.
- Failed runs store actionable error details.

## Quality Gates

- Unit tests for mapping and upsert behavior.
- Integration test with mock API.
- Structured logs per sync step.
