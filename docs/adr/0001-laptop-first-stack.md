# ADR 0001: Laptop-first stack

## Status
Accepted

## Context

Project is developed primarily on a MacBook Air M1 with 16 GB RAM.
We need high productivity and low operational complexity while preserving a path to scale.

## Decision

Use:

- FastAPI for HTTP API
- SQLite + FTS5 for source-of-truth and lexical search
- local vector abstraction (`numpy` baseline) with pluggable backend
- Alembic for schema migration
- `venv`, `pip`, `ruff`, `mypy`, `pytest`, `pre-commit` for engineering quality

## Consequences

- Fast startup and low memory footprint.
- Easy local debugging and CI parity.
- Later migration path to Postgres/OpenSearch/Qdrant remains open without breaking API layer.
