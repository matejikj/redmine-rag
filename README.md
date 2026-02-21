# redmine-rag

Agent-first platform for retrieving Redmine knowledge (issues, journals, wiki), generating grounded answers, and attaching source citations.

## Goals

- Ingest Redmine data incrementally (`updated_on` based sync).
- Build hybrid retrieval (FTS + vector similarity).
- Generate answers grounded in retrieved chunks.
- Enforce citations per claim and keep full auditability.

## Tech Stack (optimized for MacBook Air M1, 16 GB)

- API: FastAPI
- Storage: SQLite (WAL) + FTS5
- Vectors: local index abstraction (`numpy` baseline, pluggable backend)
- Migrations: Alembic
- Worker: lightweight async scheduler/CLI jobs
- Tooling: `uv`, `ruff`, `mypy`, `pytest`, `pre-commit`

## Quick start

```bash
cp .env.example .env
make bootstrap
make migrate
make dev
```

Open `http://127.0.0.1:8000/docs`.

## Docker (optional)

```bash
docker compose up --build
```

## Common commands

```bash
make format
make lint
make typecheck
make test
make check
make sync
make eval
```

## Project layout

- `src/redmine_rag/` application code
- `migrations/` Alembic migration scripts
- `tests/` test suite
- `docs/` architecture and runbooks
- `docs/data-model.md` normalized and raw data model reference
- `prompts/` reusable prompt assets
- `evals/` evaluation datasets
- `scripts/` bootstrap and CI scripts

## API contracts (initial)

- `GET /healthz`
- `POST /v1/ask`
- `POST /v1/sync/redmine`
- `POST /v1/extract/properties`

## Agent-first development

Read `AGENTS.md` and `docs/agent-workflow.md` before implementing features.
