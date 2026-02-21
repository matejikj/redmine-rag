# Project Tasks (1-20)

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
11. `11-ollama-provider-and-local-llm-runtime.md`
12. `12-llm-grounded-answer-synthesis.md`
13. `13-llm-query-understanding-and-retrieval-planner.md`
14. `14-llm-safety-guardrails-and-output-validation.md`
15. `15-llm-observability-cost-and-fallback-control.md`
16. `16-ui-foundation-and-design-system.md`
17. `17-ui-sync-and-ingestion-control-center.md`
18. `18-ui-ask-workbench-and-citation-explorer.md`
19. `19-ui-metrics-extraction-and-evaluation-dashboard.md`
20. `20-ui-ops-release-and-usability-hardening.md`

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
