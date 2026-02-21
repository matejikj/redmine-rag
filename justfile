set shell := ["bash", "-cu"]
python := `if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi`

default:
  @just --list

bootstrap:
  ./scripts/bootstrap.sh

dev:
  ./scripts/dev.sh

migrate:
  {{python}} -m alembic upgrade head

format:
  {{python}} -m ruff format .

lint:
  {{python}} -m ruff check .

typecheck:
  {{python}} -m mypy src

test:
  {{python}} -m pytest

check:
  ./scripts/check.sh

sync:
  {{python}} -m redmine_rag.cli sync run

reindex:
  {{python}} -m redmine_rag.cli index reindex

eval:
  {{python}} scripts/eval/run_eval.py

mock-redmine:
  ./scripts/mock-redmine.sh
