set shell := ["bash", "-cu"]

default:
  @just --list

bootstrap:
  ./scripts/bootstrap.sh

dev:
  ./scripts/dev.sh

migrate:
  uv run alembic upgrade head

format:
  uv run ruff format .

lint:
  uv run ruff check .

typecheck:
  uv run mypy src

test:
  uv run pytest

check:
  ./scripts/check.sh

sync:
  uv run redmine-rag sync run

eval:
  python3 scripts/eval/run_eval.py

mock-redmine:
  ./scripts/mock-redmine.sh
