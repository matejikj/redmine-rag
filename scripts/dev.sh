#!/usr/bin/env bash
set -euo pipefail

mkdir -p data indexes logs
uv run uvicorn redmine_rag.main:app --reload --host 127.0.0.1 --port 8000
