# redmine-rag

Agent-first platform for retrieving Redmine knowledge (issues, journals, wiki), generating grounded answers, and attaching source citations.

## Goals

- Ingest Redmine data incrementally (`updated_on` based sync).
- Persist both raw payloads and normalized entities with idempotent upserts.
- Build hybrid retrieval (FTS + vector similarity).
- Generate answers grounded in retrieved chunks.
- Enforce citations per claim and keep full auditability.

## Tech Stack (optimized for MacBook Air M1, 16 GB)

- API: FastAPI
- Storage: SQLite (WAL) + FTS5
- Vectors: local index abstraction (`numpy` baseline, pluggable backend)
- Migrations: Alembic
- Worker: lightweight async scheduler/CLI jobs
- Tooling: `venv`, `pip`, `ruff`, `mypy`, `pytest`, `pre-commit`

## Quick start

```bash
cp .env.example .env
make bootstrap
make migrate
make dev
```

`make bootstrap` creates `.venv`, installs dependencies with `pip`, and sets git hooks.

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
make reindex
make eval
make dataset-quality
make mock-redmine
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

## Mock Redmine API

For local development without real Redmine access:

```bash
make mock-redmine
```

Then set:

```bash
REDMINE_BASE_URL=http://127.0.0.1:8081
REDMINE_API_KEY=mock-api-key
```

See `docs/runbooks/mock-redmine.md` for details.

## Ingestion module configuration

You can enable/disable ingestion modules via `.env`:

```bash
REDMINE_MODULES=projects,users,groups,trackers,issue_statuses,issue_priorities,issues,time_entries,news,documents,files,boards,wiki
REDMINE_BOARD_IDS=94001,94003
REDMINE_WIKI_PAGES=platform-core:Feature-Login,platform-core:Incident-Triage-Playbook
```

- `REDMINE_MODULES`: registry toggle for sync pipeline modules.
- `REDMINE_BOARD_IDS`: board IDs for board/message ingestion.
- `REDMINE_WIKI_PAGES`: wiki references in `project_ref:title` format.

## Chunking and FTS

- Incremental sync updates `doc_chunk` for issues, journals, wiki pages, attachments, time entries, news, documents, and board messages.
- SQLite FTS5 index is maintained by triggers on `doc_chunk`.
- For full rebuild of chunks and FTS content, run:

```bash
make reindex
```

## Agent-first development

Read `AGENTS.md` and `docs/agent-workflow.md` before implementing features.
