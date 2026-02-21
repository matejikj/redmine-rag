# Project Tasks (1-10)

This folder contains a step-by-step plan to reach a production-ready Redmine RAG platform.

## Order

1. `01-mock-redmine-api.md`
2. `02-ingestion-foundation.md`
3. `03-chunking-and-fts.md`
4. `04-embeddings-and-hybrid-retrieval.md`
5. `05-ask-endpoint-and-citations.md`
6. `06-deterministic-properties-and-metrics.md`
7. `07-llm-structured-extraction.md`
8. `08-evaluation-and-regression-gates.md`
9. `09-production-hardening-and-ops.md`
10. `10-release-cutover-and-go-live.md`

## Quality baseline for every task

- Keep changes small and reviewable.
- Add tests for all behavior changes.
- Keep API contracts explicit.
- Keep docs and runbooks updated.
- Run quality checks before merge.

## Data coverage policy

The target is full Redmine coverage, not only issues and wiki.

At minimum, the roadmap must support:
- Issues and all issue-linked data (`journals/comments`, attachments, relations, watchers, custom fields).
- Wiki pages and versions.
- Time entries.
- Projects, trackers, statuses, priorities, categories, versions, and memberships.
- Users and groups needed for attribution and filtering.
- News, documents/files, boards/messages (if enabled in Redmine).
