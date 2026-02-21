#!/usr/bin/env bash
set -euo pipefail

uv sync --group dev
uv run pre-commit install
mkdir -p data indexes logs
