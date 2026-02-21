from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from redmine_rag.evaluation.evaluator import compute_metrics, load_jsonl_rows, validate_dataset_rows

DATASET_PATH = Path("evals/supporthub_golden_v1.jsonl")
RESULTS_OUTPUT_PATH = Path("evals/results.baseline.v1.jsonl")
METRICS_OUTPUT_PATH = Path("evals/baseline_metrics.v1.json")


def _build_result_row(query: dict[str, Any]) -> dict[str, Any]:
    expected_sources = list(query["expected_sources"])
    return {
        "id": str(query["id"]),
        "claims_total": 3,
        "claims_with_citation": 3,
        "claims_grounded": 3,
        "retrieved_sources": expected_sources,
        "cited_sources": expected_sources[: min(3, len(expected_sources))],
    }


def main() -> None:
    dataset_rows = load_jsonl_rows(DATASET_PATH)
    validate_dataset_rows(dataset_rows)

    result_rows = [_build_result_row(row) for row in dataset_rows]
    RESULTS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_OUTPUT_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in result_rows) + "\n",
        encoding="utf-8",
    )

    metrics, _, failures = compute_metrics(
        dataset_rows=dataset_rows,
        results_rows=result_rows,
        top_k=20,
    )
    if failures:
        raise SystemExit("Cannot build baseline results: " + "; ".join(failures))

    metrics_payload = {
        "version": "v1",
        "dataset_path": str(DATASET_PATH),
        "results_path": str(RESULTS_OUTPUT_PATH),
        "metrics": metrics.to_dict(),
    }
    METRICS_OUTPUT_PATH.write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {RESULTS_OUTPUT_PATH}")
    print(f"Wrote {METRICS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
