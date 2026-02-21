#!/usr/bin/env bash
set -euo pipefail

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

mkdir -p data indexes logs
exec "${PYTHON_BIN}" -m uvicorn redmine_rag.main:app --reload --host 127.0.0.1 --port 8000
