from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from redmine_rag.api.schemas import (
    EvalArtifactsResponse,
    EvalComparisonRow,
    EvalMetricsSnapshot,
)
from redmine_rag.evaluation.evaluator import EvalMetrics, compare_metrics

DEFAULT_ALLOWED_DROP = {
    "citation_coverage": 0.01,
    "groundedness": 0.01,
    "retrieval_hit_rate": 0.02,
}

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CURRENT_REPORT_PATH = _REPO_ROOT / "evals" / "reports" / "latest_eval_report.json"
_REGRESSION_GATE_PATH = _REPO_ROOT / "evals" / "reports" / "latest_regression_gate.json"
_BASELINE_PATH = _REPO_ROOT / "evals" / "baseline_metrics.v1.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return payload


def _as_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return float(stripped)
        except ValueError:
            return default
    return default


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return int(stripped)
        except ValueError:
            return default
    return default


def _parse_source_type_coverage(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, int] = {}
    for key, raw in value.items():
        normalized[str(key)] = _as_int(raw)
    return normalized


def _parse_metrics_snapshot(payload: dict[str, Any] | None) -> EvalMetricsSnapshot | None:
    if payload is None:
        return None
    metrics_raw = payload.get("metrics", payload)
    if not isinstance(metrics_raw, dict):
        return None
    return EvalMetricsSnapshot(
        query_count=_as_int(metrics_raw.get("query_count")),
        citation_coverage=_as_float(metrics_raw.get("citation_coverage")),
        groundedness=_as_float(metrics_raw.get("groundedness")),
        retrieval_hit_rate=_as_float(metrics_raw.get("retrieval_hit_rate")),
        source_type_coverage=_parse_source_type_coverage(metrics_raw.get("source_type_coverage")),
    )


def _snapshot_to_eval_metrics(snapshot: EvalMetricsSnapshot) -> EvalMetrics:
    return EvalMetrics(
        query_count=snapshot.query_count,
        citation_coverage=snapshot.citation_coverage,
        groundedness=snapshot.groundedness,
        retrieval_hit_rate=snapshot.retrieval_hit_rate,
        source_type_coverage=snapshot.source_type_coverage,
    )


def _parse_allowed_drop(gate_payload: dict[str, Any] | None) -> dict[str, float]:
    if gate_payload is None:
        return dict(DEFAULT_ALLOWED_DROP)
    comparisons = gate_payload.get("comparisons")
    if not isinstance(comparisons, list):
        return dict(DEFAULT_ALLOWED_DROP)

    allowed_drop = dict(DEFAULT_ALLOWED_DROP)
    for row in comparisons:
        if not isinstance(row, dict):
            continue
        metric = str(row.get("metric", "")).strip()
        if metric not in allowed_drop:
            continue
        allowed_drop[metric] = _as_float(row.get("allowed_drop"), allowed_drop[metric])
    return allowed_drop


def _read_string_list(payload: dict[str, Any] | None, key: str) -> list[str]:
    if payload is None:
        return []
    raw = payload.get(key)
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw]


async def get_eval_artifacts_summary() -> EvalArtifactsResponse:
    current_payload = _load_json(_CURRENT_REPORT_PATH)
    baseline_payload = _load_json(_BASELINE_PATH)
    regression_payload = _load_json(_REGRESSION_GATE_PATH)

    notes: list[str] = []
    if current_payload is None:
        notes.append(f"Current eval report missing: {_CURRENT_REPORT_PATH}")
    if baseline_payload is None:
        notes.append(f"Baseline metrics missing: {_BASELINE_PATH}")
    if regression_payload is None:
        notes.append(f"Regression gate report missing: {_REGRESSION_GATE_PATH}")

    current_metrics = _parse_metrics_snapshot(current_payload)
    baseline_metrics = _parse_metrics_snapshot(baseline_payload)

    comparisons: list[EvalComparisonRow] = []
    failures: list[str] = []
    if current_metrics is not None and baseline_metrics is not None:
        allowed_drop = _parse_allowed_drop(regression_payload)
        comparison_rows, computed_failures = compare_metrics(
            baseline=_snapshot_to_eval_metrics(baseline_metrics),
            current=_snapshot_to_eval_metrics(current_metrics),
            allowed_drop=allowed_drop,
        )
        comparisons = [
            EvalComparisonRow(
                metric=row.metric,
                baseline=row.baseline,
                current=row.current,
                delta=row.delta,
                allowed_drop=row.allowed_drop,
                passed=row.passed,
            )
            for row in comparison_rows
        ]
        failures.extend(computed_failures)

    gate_failures = _read_string_list(regression_payload, "failures")
    llm_runtime_failures = _read_string_list(regression_payload, "llm_runtime_failures")
    failures.extend(gate_failures)
    failures.extend(llm_runtime_failures)
    failures = sorted(set(failures))

    status: Literal["pass", "fail", "missing"]
    if current_metrics is None or baseline_metrics is None:
        status = "missing"
    elif failures:
        status = "fail"
    else:
        status = "pass"

    return EvalArtifactsResponse(
        generated_at=datetime.now(UTC),
        status=status,
        current_report_path=str(_CURRENT_REPORT_PATH) if current_payload is not None else None,
        baseline_path=str(_BASELINE_PATH) if baseline_payload is not None else None,
        regression_gate_path=str(_REGRESSION_GATE_PATH) if regression_payload is not None else None,
        current_metrics=current_metrics,
        baseline_metrics=baseline_metrics,
        comparisons=comparisons,
        failures=failures,
        llm_runtime_failures=llm_runtime_failures,
        notes=notes,
    )
