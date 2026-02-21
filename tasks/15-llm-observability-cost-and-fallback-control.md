# Task 15: LLM Observability, Cost, and Fallback Control

## Goal

Make LLM behavior transparent, budget-aware, and operationally safe.

## Scope

- Capture LLM latency, token estimates, error buckets, and success rate.
- Enforce per-request and per-run budget limits.
- Add adaptive fallback rules when LLM is slow/unavailable.
- Expose LLM runtime metrics for operations and release gates.

## Deliverables

- Structured LLM telemetry events and counters.
- Configurable limits for timeout, retries, and cost budget.
- Circuit-breaker style fallback to deterministic answer mode.
- Ops runbook for diagnosing degraded LLM runtime.

## Acceptance Criteria

- LLM failures degrade gracefully without breaking API contract.
- Budget exceedance is visible and enforced.
- Regression gate includes LLM reliability and latency thresholds.
- Operators can identify failure mode from logs/metrics alone.

## Quality Gates

- Failure injection tests (timeouts, invalid payloads, model unavailable).
- Performance test with repeated ask/extract calls under load.
- Documentation for SLO/SLA targets and alert thresholds.
