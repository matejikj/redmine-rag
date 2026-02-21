# Task 06: Deterministic Properties and Workflow Metrics

## Goal

Extract objective metrics and structured properties without LLM dependency.

## Scope

- Compute workflow metrics from issue/journal events.
- Fill `issue_metric` table.
- Define base property schema for downstream analytics.

## Deliverables

- Metrics extractor job (`first_response_s`, `resolution_s`, `reopen_count`, etc.).
- Data quality checks for timestamp/state anomalies.
- API/read model for analytical summaries.

## Acceptance Criteria

- Metrics are reproducible and explainable.
- Edge cases (reopened issues, missing states) are handled.
- Aggregations by project/time range are available.

## Quality Gates

- Unit tests with timeline fixtures.
- Validation rules for invalid transitions.
- Clear formulas documented in docs.
