PYTHON ?= python3
UV ?= uv

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
	@echo "  make mock-redmine - run local Mock Redmine API"

bootstrap:
	./scripts/bootstrap.sh

dev:
	./scripts/dev.sh

migrate:
	$(UV) run alembic upgrade head

revision:
	@test -n "$(msg)" || (echo "Usage: make revision msg=\"description\"" && exit 1)
	$(UV) run alembic revision --autogenerate -m "$(msg)"

format:
	$(UV) run ruff format .

lint:
	$(UV) run ruff check .

typecheck:
	$(UV) run mypy src

test:
	$(UV) run pytest

check: lint typecheck test

sync:
	$(UV) run redmine-rag sync run

eval:
	$(PYTHON) scripts/eval/run_eval.py

mock-redmine:
	./scripts/mock-redmine.sh
