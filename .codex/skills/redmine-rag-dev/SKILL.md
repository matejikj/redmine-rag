# redmine-rag-dev

## Purpose

Use this skill when implementing features in the Redmine RAG project with strict grounding and citation requirements.

## Workflow

1. Read `docs/architecture.md` and `AGENTS.md`.
2. If schema changes are needed, add Alembic migration first.
3. Implement service logic in `src/redmine_rag/services/`.
4. Keep API handlers thin in `src/redmine_rag/api/router.py`.
5. Add or update tests in `tests/`.
6. Update docs (`README.md` + relevant runbook/ADR).

## Commands

- `make migrate`
- `make check`
- `make sync`
- `make eval`

## Guardrails

- No unsupported claims in generated answers.
- Every claim must be traceable to source chunks.
- Keep retrieval deterministic and auditable.
