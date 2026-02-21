# Agent Development Workflow

1. Read context first.
Review `AGENTS.md`, relevant docs, and the target files before changing code.

2. Plan a small vertical slice.
Define one clear goal that can be implemented, tested, and reviewed quickly.

3. Implement in small steps.
Keep API handlers thin, put logic in services, and keep changes focused.

4. Validate continuously.
Run migrations/tests/lint locally (`make migrate`, `make check`) before opening a PR.

5. Keep outputs grounded.
For RAG features, ensure answers are based only on retrieved sources and always include citations.

6. Document every meaningful change.
Update README/runbooks/ADR when behavior, architecture, or workflows change.

7. Ship with traceability.
Open a PR with clear summary, risks, and validation results.
