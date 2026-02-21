# Task 08: Evaluation and Regression Gates

## Goal

Operationalize quality evaluation for retrieval and answer grounding.

## Scope

- Build eval runner over curated query set.
- Measure citation coverage, groundedness, retrieval hit rate.
- Add CI gate to block regressions.

## Deliverables

- Eval dataset (`jsonl`) with expected evidence targets.
- Evaluation script and report output.
- CI workflow step for non-regression threshold checks.

## Acceptance Criteria

- Eval runs locally and in CI.
- Baseline metrics are stored and versioned.
- Regressions fail the pipeline with clear diagnostics.

## Quality Gates

- Deterministic eval fixtures.
- Metrics documented in `docs/evaluation.md`.
- Team can add new eval queries safely.
