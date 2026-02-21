# Task 13: LLM Query Understanding and Retrieval Planner

## Goal

Improve retrieval quality by using LLM to rewrite user queries into retrieval-friendly plans.

## Scope

- Add optional planning step before hybrid retrieval.
- Generate normalized query, synonyms, and focused sub-queries.
- Extract candidate filters (`project`, `status`, `tracker`, time hints) from user text.
- Keep full traceability of planner output in diagnostics.

## Deliverables

- Planner schema (`normalized_query`, `expansions`, `filters`, `confidence`).
- Retrieval service integration with bounded expansion strategy.
- Debug fields in ask diagnostics for planner contribution.
- Config flags to enable/disable planner and tune max expansions.

## Acceptance Criteria

- Planner output is deterministic enough for testing (temperature and schema constraints).
- Retrieval recall improves on targeted eval subset vs baseline.
- Planner cannot add filters outside allowed domain values.
- Ask endpoint still works when planner is disabled or fails.

## Quality Gates

- Eval benchmarks comparing retrieval hit-rate with/without planner.
- Tests for invalid planner outputs and graceful fallback.
- Logs include planner mode, latency, and selected expansions.
