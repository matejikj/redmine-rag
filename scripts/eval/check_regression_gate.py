from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from redmine_rag.evaluation.evaluator import EvalMetrics, compare_metrics

DEFAULT_BASELINE = Path("evals/baseline_metrics.v1.json")
DEFAULT_CURRENT = Path("evals/reports/latest_eval_report.json")


def _load_metrics(path: Path) -> EvalMetrics:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics_raw = payload.get("metrics", payload)
    if not isinstance(metrics_raw, dict):
        raise SystemExit(f"Invalid metrics payload in {path}")

    try:
        return EvalMetrics(
            query_count=int(metrics_raw.get("query_count", 0)),
            citation_coverage=float(metrics_raw["citation_coverage"]),
            groundedness=float(metrics_raw["groundedness"]),
            retrieval_hit_rate=float(metrics_raw["retrieval_hit_rate"]),
            source_type_coverage=dict(metrics_raw.get("source_type_coverage", {})),
        )
    except KeyError as exc:
        raise SystemExit(f"Missing key in metrics payload {path}: {exc}") from exc


def _serialize_comparisons(rows: list[Any]) -> list[dict[str, Any]]:
    return [row.to_dict() for row in rows]


def _load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid JSON payload in {path}")
    return payload


def _evaluate_llm_runtime_gate(
    *,
    current_payload: dict[str, Any],
    max_llm_error_rate: float | None,
    max_llm_p95_latency_ms: int | None,
    require_llm_circuit_closed: bool,
) -> list[str]:
    if (
        max_llm_error_rate is None
        and max_llm_p95_latency_ms is None
        and not require_llm_circuit_closed
    ):
        return []

    llm_runtime = current_payload.get("llm_runtime")
    if not isinstance(llm_runtime, dict):
        return ["llm_runtime metrics missing in current report"]

    failures: list[str] = []
    attempted_calls = int(llm_runtime.get("attempted_calls", 0))
    failed_calls = int(llm_runtime.get("failed_calls", 0))
    p95_latency_ms_raw = llm_runtime.get("p95_latency_ms")
    p95_latency_ms = int(p95_latency_ms_raw) if p95_latency_ms_raw is not None else None
    circuit = llm_runtime.get("circuit")
    circuit_state = str(circuit.get("state", "unknown")) if isinstance(circuit, dict) else "unknown"

    error_rate = 0.0 if attempted_calls <= 0 else (failed_calls / attempted_calls)
    if max_llm_error_rate is not None and error_rate > max_llm_error_rate:
        failures.append(f"llm_error_rate {error_rate:.3f} > threshold {max_llm_error_rate:.3f}")
    if max_llm_p95_latency_ms is not None:
        if p95_latency_ms is None:
            failures.append("llm_p95_latency_ms missing in current report")
        elif p95_latency_ms > max_llm_p95_latency_ms:
            failures.append(
                f"llm_p95_latency_ms {p95_latency_ms} > threshold {max_llm_p95_latency_ms}"
            )
    if require_llm_circuit_closed and circuit_state != "closed":
        failures.append(f"llm_circuit_state is {circuit_state}, expected closed")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Check eval metrics against baseline")
    parser.add_argument(
        "--current", default=str(DEFAULT_CURRENT), help="Current evaluation report JSON"
    )
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE), help="Baseline metrics JSON")
    parser.add_argument(
        "--max-drop-citation-coverage",
        type=float,
        default=0.01,
        help="Maximum allowed absolute drop from baseline citation coverage",
    )
    parser.add_argument(
        "--max-drop-groundedness",
        type=float,
        default=0.01,
        help="Maximum allowed absolute drop from baseline groundedness",
    )
    parser.add_argument(
        "--max-drop-retrieval-hit-rate",
        type=float,
        default=0.02,
        help="Maximum allowed absolute drop from baseline retrieval hit rate",
    )
    parser.add_argument(
        "--report-out",
        default="evals/reports/latest_regression_gate.json",
        help="Path for structured regression diagnostics report",
    )
    parser.add_argument(
        "--max-llm-error-rate",
        type=float,
        default=None,
        help="Optional maximum allowed LLM runtime error rate for current report",
    )
    parser.add_argument(
        "--max-llm-p95-latency-ms",
        type=int,
        default=None,
        help="Optional maximum allowed LLM runtime p95 latency in milliseconds",
    )
    parser.add_argument(
        "--require-llm-circuit-closed",
        action="store_true",
        help="Fail gate when LLM circuit breaker is open",
    )
    args = parser.parse_args()

    current_path = Path(args.current)
    baseline_path = Path(args.baseline)
    if not current_path.exists():
        raise SystemExit(f"Current report does not exist: {current_path}")
    if not baseline_path.exists():
        raise SystemExit(f"Baseline report does not exist: {baseline_path}")

    current_payload = _load_payload(current_path)
    current_metrics = _load_metrics(current_path)
    baseline_metrics = _load_metrics(baseline_path)

    comparisons, failures = compare_metrics(
        baseline=baseline_metrics,
        current=current_metrics,
        allowed_drop={
            "citation_coverage": args.max_drop_citation_coverage,
            "groundedness": args.max_drop_groundedness,
            "retrieval_hit_rate": args.max_drop_retrieval_hit_rate,
        },
    )

    print("Regression gate comparison:")
    for row in comparisons:
        status = "PASS" if row.passed else "FAIL"
        print(
            f"  {row.metric}: current={row.current:.3f}, baseline={row.baseline:.3f}, "
            f"delta={row.delta:.3f}, allowed_drop={row.allowed_drop:.3f} [{status}]"
        )

    llm_runtime_failures = _evaluate_llm_runtime_gate(
        current_payload=current_payload,
        max_llm_error_rate=args.max_llm_error_rate,
        max_llm_p95_latency_ms=args.max_llm_p95_latency_ms,
        require_llm_circuit_closed=args.require_llm_circuit_closed,
    )
    all_failures = [*failures, *llm_runtime_failures]

    report_payload = {
        "current_report": str(current_path),
        "baseline_report": str(baseline_path),
        "comparisons": _serialize_comparisons(comparisons),
        "llm_runtime_failures": llm_runtime_failures,
        "passed": not all_failures,
        "failures": all_failures,
    }
    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote regression gate report to {report_path}")

    if all_failures:
        raise SystemExit("Regression gate failed: " + "; ".join(all_failures))


if __name__ == "__main__":
    main()
