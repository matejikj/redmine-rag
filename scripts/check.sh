#!/usr/bin/env bash
set -euo pipefail

uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
uv run python scripts/eval/check_mock_dataset_quality.py --all-profiles
