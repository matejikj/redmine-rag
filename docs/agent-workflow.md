# Agent Workflow

## Standard loop

1. Read `AGENTS.md` and relevant architecture docs.
2. Create a short execution plan before large edits.
3. Implement smallest vertical slice that is testable.
4. Run `make check`.
5. Update docs and migration if schema changed.

## Agent-first coding conventions

- Keep files focused and small.
- Expose explicit interfaces for services.
- Add typing to all public functions.
- Prefer deterministic behavior over hidden heuristics.

## PR checklist

- [ ] endpoint/API contract covered by tests
- [ ] migrations included if database schema changed
- [ ] logs added for background/sync paths
- [ ] docs updated (`README` and targeted runbook)
