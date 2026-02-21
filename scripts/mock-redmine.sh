#!/usr/bin/env bash
set -euo pipefail

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

PORT="${MOCK_REDMINE_PORT:-8081}"
HOST="${MOCK_REDMINE_HOST:-127.0.0.1}"

export MOCK_REDMINE_API_KEY="${MOCK_REDMINE_API_KEY:-mock-api-key}"

exec "${PYTHON_BIN}" -m uvicorn redmine_rag.mock_redmine.app:app --reload --host "${HOST}" --port "${PORT}"
