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
	@echo "  make reindex     - rebuild doc chunks and FTS index"
	@echo "  make embed       - refresh vector embeddings"
	@echo "  make eval        - run local eval scaffold"
	@echo "  make eval-baseline - rebuild baseline eval artifacts"
	@echo "  make eval-gate   - run regression gate against baseline"
	@echo "  make dataset-quality - validate dataset quality constraints"
	@echo "  make soak-medium - run medium-profile sync soak test"
	@echo "  make backup      - create local state backup snapshot"
	@echo "  make maintenance - run SQLite maintenance (checkpoint/vacuum/analyze)"
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

reindex:
	$(RUNNER) -m redmine_rag.cli index reindex

embed:
	$(RUNNER) -m redmine_rag.cli index embeddings

eval:
	$(RUNNER) scripts/eval/run_eval.py

eval-baseline:
	$(RUNNER) scripts/eval/build_baseline_results.py

eval-gate:
	$(RUNNER) scripts/eval/run_eval.py --results evals/results.baseline.v1.jsonl --report-out evals/reports/latest_eval_report.json
	$(RUNNER) scripts/eval/check_regression_gate.py --current evals/reports/latest_eval_report.json --baseline evals/baseline_metrics.v1.json

dataset-quality:
	$(RUNNER) scripts/eval/check_mock_dataset_quality.py --all-profiles

soak-medium:
	$(RUNNER) scripts/ops/soak_sync.py --iterations 3 --project-id 1

backup:
	$(RUNNER) -m redmine_rag.cli ops backup --output-dir backups

maintenance:
	$(RUNNER) -m redmine_rag.cli ops maintenance

mock-redmine:
	./scripts/mock-redmine.sh
