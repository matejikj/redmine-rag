PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
RUNNER := $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(PYTHON))

.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  make bootstrap   - install dependencies and git hooks"
	@echo "  make dev         - run FastAPI with auto-reload"
	@echo "  make migrate     - run alembic migrations"
	@echo "  make revision    - create alembic revision (msg=...)"
	@echo "  make format      - format code"
	@echo "  make lint        - lint code"
	@echo "  make typecheck   - run mypy"
	@echo "  make test        - run tests"
	@echo "  make check       - run all checks"
	@echo "  make sync        - trigger Redmine sync"
	@echo "  make eval        - run local eval scaffold"
	@echo "  make dataset-quality - validate dataset quality constraints"
	@echo "  make mock-redmine - run local Mock Redmine API"

bootstrap:
	./scripts/bootstrap.sh

dev:
	./scripts/dev.sh

migrate:
	$(RUNNER) -m alembic upgrade head

revision:
	@test -n "$(msg)" || (echo "Usage: make revision msg=\"description\"" && exit 1)
	$(RUNNER) -m alembic revision --autogenerate -m "$(msg)"

format:
	$(RUNNER) -m ruff format .

lint:
	$(RUNNER) -m ruff check .

typecheck:
	$(RUNNER) -m mypy src

test:
	$(RUNNER) -m pytest

check: lint typecheck test

sync:
	$(RUNNER) -m redmine_rag.cli sync run

eval:
	$(RUNNER) scripts/eval/run_eval.py

dataset-quality:
	$(RUNNER) scripts/eval/check_mock_dataset_quality.py --all-profiles

mock-redmine:
	./scripts/mock-redmine.sh
