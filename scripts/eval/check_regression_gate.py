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
    args = parser.parse_args()

    current_path = Path(args.current)
    baseline_path = Path(args.baseline)
    if not current_path.exists():
        raise SystemExit(f"Current report does not exist: {current_path}")
    if not baseline_path.exists():
        raise SystemExit(f"Baseline report does not exist: {baseline_path}")

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

    report_payload = {
        "current_report": str(current_path),
        "baseline_report": str(baseline_path),
        "comparisons": _serialize_comparisons(comparisons),
        "passed": not failures,
        "failures": failures,
    }
    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote regression gate report to {report_path}")

    if failures:
        raise SystemExit("Regression gate failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
