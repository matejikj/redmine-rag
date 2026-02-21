from __future__ import annotations

import logging
import math
from collections import Counter, deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any

DEFAULT_INPUT_PRICE_PER_1K_USD = 0.0006
DEFAULT_OUTPUT_PRICE_PER_1K_USD = 0.0006
_MIN_TOKEN_ESTIMATE = 1

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _RuntimeControls:
    circuit_breaker_enabled: bool = True
    circuit_failure_threshold: int = 3
    circuit_slow_threshold_ms: int = 15_000
    circuit_slow_threshold_hits: int = 3
    circuit_open_seconds: float = 60.0
    telemetry_latency_window: int = 200


@dataclass(slots=True, frozen=True)
class LlmCircuitSnapshot:
    enabled: bool
    state: str
    reason: str | None
    open_for_s: float
    opens_total: int
    consecutive_failures: int
    consecutive_slow: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "state": self.state,
            "reason": self.reason,
            "open_for_s": self.open_for_s,
            "opens_total": self.opens_total,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_slow": self.consecutive_slow,
        }


@dataclass(slots=True, frozen=True)
class LlmTelemetrySnapshot:
    attempted_calls: int
    success_calls: int
    failed_calls: int
    skipped_calls: int
    success_rate: float
    avg_latency_ms: float | None
    p95_latency_ms: int | None
    max_latency_ms: int | None
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    budget_limit_usd: float
    budget_remaining_usd: float | None
    error_buckets: dict[str, int]
    fallback_buckets: dict[str, int]
    circuit: LlmCircuitSnapshot

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempted_calls": self.attempted_calls,
            "success_calls": self.success_calls,
            "failed_calls": self.failed_calls,
            "skipped_calls": self.skipped_calls,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "budget_limit_usd": self.budget_limit_usd,
            "budget_remaining_usd": self.budget_remaining_usd,
            "error_buckets": self.error_buckets,
            "fallback_buckets": self.fallback_buckets,
            "circuit": self.circuit.to_dict(),
        }


@dataclass(slots=True)
class _TelemetryState:
    attempted_calls: int
    success_calls: int
    failed_calls: int
    skipped_calls: int
    latency_ms_total: int
    latency_samples: deque[int]
    max_latency_ms: int | None
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    error_buckets: Counter[str]
    fallback_buckets: Counter[str]
    circuit_open_until: float | None
    circuit_reason: str | None
    circuit_open_count: int
    consecutive_failures: int
    consecutive_slow: int
    controls: _RuntimeControls


_LOCK = Lock()
_STATE = _TelemetryState(
    attempted_calls=0,
    success_calls=0,
    failed_calls=0,
    skipped_calls=0,
    latency_ms_total=0,
    latency_samples=deque(maxlen=200),
    max_latency_ms=None,
    estimated_input_tokens=0,
    estimated_output_tokens=0,
    estimated_cost_usd=0.0,
    error_buckets=Counter(),
    fallback_buckets=Counter(),
    circuit_open_until=None,
    circuit_reason=None,
    circuit_open_count=0,
    consecutive_failures=0,
    consecutive_slow=0,
    controls=_RuntimeControls(),
)


def configure_llm_runtime_controls(
    *,
    circuit_breaker_enabled: bool,
    circuit_failure_threshold: int,
    circuit_slow_threshold_ms: int,
    circuit_slow_threshold_hits: int,
    circuit_open_seconds: float,
    telemetry_latency_window: int,
) -> None:
    with _LOCK:
        _STATE.controls = _RuntimeControls(
            circuit_breaker_enabled=circuit_breaker_enabled,
            circuit_failure_threshold=max(1, circuit_failure_threshold),
            circuit_slow_threshold_ms=max(1, circuit_slow_threshold_ms),
            circuit_slow_threshold_hits=max(1, circuit_slow_threshold_hits),
            circuit_open_seconds=max(0.0, circuit_open_seconds),
            telemetry_latency_window=max(1, telemetry_latency_window),
        )
        if _STATE.latency_samples.maxlen != _STATE.controls.telemetry_latency_window:
            _STATE.latency_samples = deque(
                _STATE.latency_samples,
                maxlen=_STATE.controls.telemetry_latency_window,
            )


def reset_llm_telemetry() -> None:
    with _LOCK:
        _STATE.attempted_calls = 0
        _STATE.success_calls = 0
        _STATE.failed_calls = 0
        _STATE.skipped_calls = 0
        _STATE.latency_ms_total = 0
        _STATE.latency_samples.clear()
        _STATE.max_latency_ms = None
        _STATE.estimated_input_tokens = 0
        _STATE.estimated_output_tokens = 0
        _STATE.estimated_cost_usd = 0.0
        _STATE.error_buckets.clear()
        _STATE.fallback_buckets.clear()
        _STATE.circuit_open_until = None
        _STATE.circuit_reason = None
        _STATE.circuit_open_count = 0
        _STATE.consecutive_failures = 0
        _STATE.consecutive_slow = 0


def estimate_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return _MIN_TOKEN_ESTIMATE
    return max(_MIN_TOKEN_ESTIMATE, int(math.ceil(len(stripped) / 0.75)))


def estimate_cost_usd(
    *,
    input_tokens: int,
    output_tokens: int,
    input_price_per_1k_usd: float = DEFAULT_INPUT_PRICE_PER_1K_USD,
    output_price_per_1k_usd: float = DEFAULT_OUTPUT_PRICE_PER_1K_USD,
) -> float:
    normalized_input = max(0, input_tokens)
    normalized_output = max(0, output_tokens)
    cost = (normalized_input / 1000.0) * max(input_price_per_1k_usd, 0.0) + (
        normalized_output / 1000.0
    ) * max(output_price_per_1k_usd, 0.0)
    return round(cost, 6)


def allow_llm_execution(
    *,
    estimated_cost_usd: float,
    budget_limit_usd: float,
) -> tuple[bool, str | None]:
    with _LOCK:
        now = monotonic()
        _refresh_circuit_state_locked(now)
        if _is_circuit_open_locked(now):
            return False, "circuit_open"
        projected_cost = _STATE.estimated_cost_usd + max(estimated_cost_usd, 0.0)
        budget_limit = max(budget_limit_usd, 0.0)
        if budget_limit_usd > 0 and projected_cost > budget_limit:
            return False, "cost_budget_exceeded"
        return True, None


def record_llm_success(
    *,
    llm_component: str,
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
) -> None:
    with _LOCK:
        now = monotonic()
        _refresh_circuit_state_locked(now)
        _STATE.attempted_calls += 1
        _STATE.success_calls += 1
        _record_latency_locked(latency_ms)
        _record_usage_locked(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
        _STATE.consecutive_failures = 0
        if latency_ms >= _STATE.controls.circuit_slow_threshold_ms:
            _STATE.consecutive_slow += 1
        else:
            _STATE.consecutive_slow = 0

        if (
            _STATE.controls.circuit_breaker_enabled
            and _STATE.consecutive_slow >= _STATE.controls.circuit_slow_threshold_hits
        ):
            _open_circuit_locked(reason="slow_runtime", now=now)

    logger.info(
        "LLM runtime success",
        extra={
            "llm_event": "success",
            "llm_component": llm_component,
            "llm_latency_ms": latency_ms,
            "llm_input_tokens_est": input_tokens,
            "llm_output_tokens_est": output_tokens,
            "llm_estimated_cost_usd": estimated_cost_usd,
        },
    )


def record_llm_failure(
    *,
    llm_component: str,
    error_bucket: str,
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
) -> None:
    with _LOCK:
        now = monotonic()
        _refresh_circuit_state_locked(now)
        _STATE.attempted_calls += 1
        _STATE.failed_calls += 1
        _STATE.error_buckets[error_bucket] += 1
        _record_latency_locked(latency_ms)
        _record_usage_locked(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )
        _STATE.consecutive_failures += 1
        _STATE.consecutive_slow = 0
        if (
            _STATE.controls.circuit_breaker_enabled
            and _STATE.consecutive_failures >= _STATE.controls.circuit_failure_threshold
        ):
            _open_circuit_locked(reason=error_bucket, now=now)

    logger.warning(
        "LLM runtime failure",
        extra={
            "llm_event": "failure",
            "llm_component": llm_component,
            "llm_error_bucket": error_bucket,
            "llm_latency_ms": latency_ms,
            "llm_input_tokens_est": input_tokens,
            "llm_output_tokens_est": output_tokens,
            "llm_estimated_cost_usd": estimated_cost_usd,
        },
    )


def record_llm_fallback(*, llm_component: str, reason: str) -> None:
    with _LOCK:
        _STATE.skipped_calls += 1
        _STATE.fallback_buckets[reason] += 1
    logger.warning(
        "LLM fallback activated",
        extra={
            "llm_event": "fallback",
            "llm_component": llm_component,
            "llm_fallback_reason": reason,
        },
    )


def get_llm_telemetry_snapshot(*, budget_limit_usd: float) -> LlmTelemetrySnapshot:
    with _LOCK:
        now = monotonic()
        _refresh_circuit_state_locked(now)
        attempted_calls = _STATE.attempted_calls
        success_calls = _STATE.success_calls
        failed_calls = _STATE.failed_calls
        skipped_calls = _STATE.skipped_calls
        success_rate = (success_calls / attempted_calls) if attempted_calls > 0 else 1.0
        avg_latency_ms = (
            round(_STATE.latency_ms_total / attempted_calls, 2) if attempted_calls > 0 else None
        )
        p95_latency_ms = _p95_latency_ms(list(_STATE.latency_samples))
        max_latency_ms = _STATE.max_latency_ms
        estimated_cost_usd = round(_STATE.estimated_cost_usd, 6)
        budget_remaining_usd = None
        if budget_limit_usd > 0:
            budget_remaining_usd = round(max(budget_limit_usd - estimated_cost_usd, 0.0), 6)

        open_for_s = 0.0
        circuit_state = "closed"
        if _is_circuit_open_locked(now):
            circuit_state = "open"
            assert _STATE.circuit_open_until is not None
            open_for_s = round(max(_STATE.circuit_open_until - now, 0.0), 3)

        circuit = LlmCircuitSnapshot(
            enabled=_STATE.controls.circuit_breaker_enabled,
            state=circuit_state,
            reason=_STATE.circuit_reason,
            open_for_s=open_for_s,
            opens_total=_STATE.circuit_open_count,
            consecutive_failures=_STATE.consecutive_failures,
            consecutive_slow=_STATE.consecutive_slow,
        )

        return LlmTelemetrySnapshot(
            attempted_calls=attempted_calls,
            success_calls=success_calls,
            failed_calls=failed_calls,
            skipped_calls=skipped_calls,
            success_rate=round(success_rate, 4),
            avg_latency_ms=avg_latency_ms,
            p95_latency_ms=p95_latency_ms,
            max_latency_ms=max_latency_ms,
            estimated_input_tokens=_STATE.estimated_input_tokens,
            estimated_output_tokens=_STATE.estimated_output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            budget_limit_usd=budget_limit_usd,
            budget_remaining_usd=budget_remaining_usd,
            error_buckets=dict(sorted(_STATE.error_buckets.items())),
            fallback_buckets=dict(sorted(_STATE.fallback_buckets.items())),
            circuit=circuit,
        )


def _refresh_circuit_state_locked(now: float) -> None:
    if _STATE.circuit_open_until is None:
        return
    if now >= _STATE.circuit_open_until:
        _STATE.circuit_open_until = None
        _STATE.circuit_reason = None
        _STATE.consecutive_failures = 0
        _STATE.consecutive_slow = 0


def _is_circuit_open_locked(now: float) -> bool:
    return _STATE.circuit_open_until is not None and now < _STATE.circuit_open_until


def _open_circuit_locked(*, reason: str, now: float) -> None:
    if not _STATE.controls.circuit_breaker_enabled:
        return
    _STATE.circuit_open_until = now + _STATE.controls.circuit_open_seconds
    _STATE.circuit_reason = reason
    _STATE.circuit_open_count += 1


def _record_latency_locked(latency_ms: int) -> None:
    safe_latency = max(0, latency_ms)
    _STATE.latency_ms_total += safe_latency
    _STATE.latency_samples.append(safe_latency)
    if _STATE.max_latency_ms is None or safe_latency > _STATE.max_latency_ms:
        _STATE.max_latency_ms = safe_latency


def _record_usage_locked(
    *,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
) -> None:
    _STATE.estimated_input_tokens += max(0, input_tokens)
    _STATE.estimated_output_tokens += max(0, output_tokens)
    _STATE.estimated_cost_usd += max(0.0, estimated_cost_usd)


def _p95_latency_ms(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, int(math.ceil(0.95 * len(ordered)) - 1))
    return int(ordered[index])
