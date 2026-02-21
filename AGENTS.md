# AGENTS.md

## Mission

Build a reliable Redmine RAG system with strict source grounding and traceable citations.

## Core rules

- Never return unsupported facts. If evidence is missing, say so explicitly.
- Every claim in user-facing answers must map to at least one source chunk.
- Keep ingestion and retrieval deterministic where possible.
- Prefer incremental sync over full reimport.

## Architecture guardrails

- SQLite is source of truth for local development.
- FTS5 drives lexical retrieval.
- Vector layer is pluggable and must expose deterministic IDs.
- API endpoints remain thin; business logic lives in services.

## Coding standards

- Python 3.12+ with full type hints on public interfaces.
- Use small functions and explicit return types.
- Avoid hidden side effects in service methods.
- Log structured events for sync/retrieval/extraction steps.

## Required checks before merge

- `make format`
- `make check`
- migration present for schema changes
- tests updated for API contract changes

## Definition of done

- feature implemented
- tests added/updated
- docs updated (`README` and relevant runbook)
- observability hooks included (logs/metrics placeholders)
