#!/usr/bin/env bash
set -euo pipefail

PORT="${MOCK_REDMINE_PORT:-8081}"
HOST="${MOCK_REDMINE_HOST:-127.0.0.1}"

export MOCK_REDMINE_API_KEY="${MOCK_REDMINE_API_KEY:-mock-api-key}"

uv run uvicorn redmine_rag.mock_redmine.app:app --reload --host "${HOST}" --port "${PORT}"
