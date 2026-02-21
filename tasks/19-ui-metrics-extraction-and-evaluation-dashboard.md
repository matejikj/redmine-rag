# Task 19: UI Metrics, Extraction, and Evaluation Dashboard

## Goal

Expose extraction quality, project metrics, and regression health in a clear operational dashboard.

## Scope

- Add metrics page for `/v1/metrics/summary` with project/date filters.
- Add extraction control panel and result summaries.
- Show LLM extraction health counters (success/fail/skip/retry).
- Add evaluation/regression status section from latest report artifacts.

## Deliverables

- Metrics charts/tables with global and per-project breakdown.
- Extraction run controls and latest run diagnostics.
- Eval gate status widget (pass/fail + key deltas).
- Export option for metrics/eval snapshots.

## Acceptance Criteria

- Product and ops users can inspect platform quality without terminal access.
- Dashboard highlights regressions and extraction anomalies quickly.
- Filters produce deterministic, reproducible views.
- Data refresh patterns are clear (auto/manual timestamps shown).

## Quality Gates

- UI integration tests for metrics and extraction flows.
- Contract tests for report parsing and empty-state handling.
- Documentation update with dashboard usage examples.
