from __future__ import annotations

from redmine_rag.services.llm_telemetry_service import (
    allow_llm_execution,
    configure_llm_runtime_controls,
    get_llm_telemetry_snapshot,
    record_llm_failure,
    record_llm_success,
    reset_llm_telemetry,
)


def test_llm_telemetry_snapshot_tracks_success_rate_and_latency() -> None:
    reset_llm_telemetry()
    configure_llm_runtime_controls(
        circuit_breaker_enabled=True,
        circuit_failure_threshold=3,
        circuit_slow_threshold_ms=5000,
        circuit_slow_threshold_hits=2,
        circuit_open_seconds=60.0,
        telemetry_latency_window=10,
    )

    record_llm_success(
        llm_component="ask",
        latency_ms=30,
        input_tokens=100,
        output_tokens=80,
        estimated_cost_usd=0.0012,
    )
    record_llm_success(
        llm_component="extract",
        latency_ms=50,
        input_tokens=90,
        output_tokens=40,
        estimated_cost_usd=0.0010,
    )
    record_llm_failure(
        llm_component="ask",
        error_bucket="timeout",
        latency_ms=120,
        input_tokens=110,
        output_tokens=0,
        estimated_cost_usd=0.0013,
    )

    snapshot = get_llm_telemetry_snapshot(budget_limit_usd=1.0)
    assert snapshot.attempted_calls == 3
    assert snapshot.success_calls == 2
    assert snapshot.failed_calls == 1
    assert snapshot.success_rate == 0.6667
    assert snapshot.p95_latency_ms == 120
    assert snapshot.error_buckets["timeout"] == 1
    assert snapshot.budget_remaining_usd is not None


def test_circuit_breaker_opens_after_failure_threshold() -> None:
    reset_llm_telemetry()
    configure_llm_runtime_controls(
        circuit_breaker_enabled=True,
        circuit_failure_threshold=2,
        circuit_slow_threshold_ms=5000,
        circuit_slow_threshold_hits=2,
        circuit_open_seconds=30.0,
        telemetry_latency_window=10,
    )

    record_llm_failure(
        llm_component="ask",
        error_bucket="provider_error",
        latency_ms=10,
        input_tokens=1,
        output_tokens=0,
        estimated_cost_usd=0.0001,
    )
    record_llm_failure(
        llm_component="ask",
        error_bucket="provider_error",
        latency_ms=12,
        input_tokens=1,
        output_tokens=0,
        estimated_cost_usd=0.0001,
    )

    allowed, reason = allow_llm_execution(estimated_cost_usd=0.0001, budget_limit_usd=1.0)
    assert allowed is False
    assert reason == "circuit_open"

    snapshot = get_llm_telemetry_snapshot(budget_limit_usd=1.0)
    assert snapshot.circuit.state == "open"
    assert snapshot.circuit.reason == "provider_error"


def test_budget_guard_blocks_when_estimated_cost_exceeds_remaining() -> None:
    reset_llm_telemetry()
    configure_llm_runtime_controls(
        circuit_breaker_enabled=True,
        circuit_failure_threshold=3,
        circuit_slow_threshold_ms=5000,
        circuit_slow_threshold_hits=2,
        circuit_open_seconds=30.0,
        telemetry_latency_window=10,
    )

    record_llm_success(
        llm_component="extract",
        latency_ms=25,
        input_tokens=100,
        output_tokens=50,
        estimated_cost_usd=0.7,
    )

    allowed, reason = allow_llm_execution(estimated_cost_usd=0.4, budget_limit_usd=1.0)
    assert allowed is False
    assert reason == "cost_budget_exceeded"
