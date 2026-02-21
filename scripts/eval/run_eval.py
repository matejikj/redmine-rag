from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from redmine_rag.evaluation.evaluator import (
    compute_metrics,
    load_jsonl_rows,
    summarize_dataset,
    validate_dataset_rows,
)

DEFAULT_DATASET = Path("evals/supporthub_golden_v1.jsonl")
CLAIM_LINE_PATTERN = re.compile(r"^\d+\.\s+")
CITATION_MARKER_PATTERN = re.compile(r"\[(\d+(?:,\s*\d+)*)\]\s*$")


def _build_ask_payload(row: dict[str, Any], top_k: int) -> dict[str, Any]:
    filters = row.get("filters", {})
    project_id = filters.get("project_id")
    project_ids: list[int] = []
    if isinstance(project_id, list):
        project_ids = [int(value) for value in project_id]
    elif project_id is not None and str(project_id).strip():
        project_ids = [int(project_id)]

    return {
        "query": str(row["query"]),
        "filters": {
            "project_ids": project_ids,
            "tracker_ids": [],
            "status_ids": [],
            "from_date": None,
            "to_date": None,
        },
        "top_k": top_k,
    }


def _parse_result_row(query_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    answer_markdown = str(payload.get("answer_markdown", ""))
    citations = list(payload.get("citations", []))

    claim_lines = [
        line.strip() for line in answer_markdown.splitlines() if CLAIM_LINE_PATTERN.match(line)
    ]
    claims_total = len(claim_lines)
    claims_with_citation = 0
    claims_grounded = 0
    cited_citation_ids: set[int] = set()
    citation_index = {int(citation["id"]): citation for citation in citations if "id" in citation}

    for line in claim_lines:
        marker_match = CITATION_MARKER_PATTERN.search(line)
        if marker_match is None:
            continue
        citation_ids = [int(value) for value in marker_match.group(1).replace(" ", "").split(",")]
        valid_ids = [citation_id for citation_id in citation_ids if citation_id in citation_index]
        if not valid_ids:
            continue
        claims_with_citation += 1
        claims_grounded += 1
        cited_citation_ids.update(valid_ids)

    cited_sources = [
        {
            "source_type": citation_index[citation_id]["source_type"],
            "source_id": citation_index[citation_id]["source_id"],
        }
        for citation_id in sorted(cited_citation_ids)
    ]
    retrieved_sources = [
        {"source_type": citation["source_type"], "source_id": citation["source_id"]}
        for citation in citations
    ]

    return {
        "id": query_id,
        "claims_total": claims_total,
        "claims_with_citation": claims_with_citation,
        "claims_grounded": claims_grounded,
        "retrieved_sources": retrieved_sources,
        "cited_sources": cited_sources,
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def _run_live_eval(
    *,
    dataset_rows: list[dict[str, Any]],
    api_base_url: str,
    top_k: int,
    timeout_s: float,
    output_results: Path,
) -> list[dict[str, Any]]:
    url = f"{api_base_url.rstrip('/')}/v1/ask"
    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=timeout_s) as client:
        for row in dataset_rows:
            query_id = str(row["id"])
            payload = _build_ask_payload(row, top_k=top_k)
            response = client.post(url, json=payload)
            if response.status_code != 200:
                raise SystemExit(
                    "Ask API failed for "
                    f"{query_id}: status={response.status_code}, body={response.text}"
                )
            result_row = _parse_result_row(query_id=query_id, payload=response.json())
            results.append(result_row)

    _write_jsonl(output_results, results)
    return results


def _load_report_metrics(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise SystemExit(f"Invalid report file: metrics missing in {path}")
    return metrics


def _fetch_llm_runtime_metrics(*, api_base_url: str, timeout_s: float) -> dict[str, Any] | None:
    url = f"{api_base_url.rstrip('/')}/healthz"
    with httpx.Client(timeout=timeout_s) as client:
        response = client.get(url)
    if response.status_code != 200:
        return None
    payload = response.json()
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        return None

    for check in checks:
        if not isinstance(check, dict):
            continue
        if check.get("name") != "llm_telemetry":
            continue
        detail_raw = check.get("detail")
        detail: dict[str, Any] = {}
        if isinstance(detail_raw, str) and detail_raw.strip():
            try:
                parsed = json.loads(detail_raw)
            except json.JSONDecodeError:
                parsed = {"raw_detail": detail_raw}
            if isinstance(parsed, dict):
                detail = parsed
        if not isinstance(detail, dict):
            detail = {}
        detail["health_status"] = str(check.get("status", "unknown"))
        detail["health_latency_ms"] = check.get("latency_ms")
        return detail
    return None


def _evaluate_thresholds(
    *,
    metrics: dict[str, Any],
    min_citation_coverage: float | None,
    min_groundedness: float | None,
    min_retrieval_hit_rate: float | None,
) -> list[str]:
    failures: list[str] = []
    citation_coverage = float(metrics.get("citation_coverage", 0.0))
    groundedness = float(metrics.get("groundedness", 0.0))
    retrieval_hit_rate = float(metrics.get("retrieval_hit_rate", 0.0))
    if min_citation_coverage is not None and citation_coverage < min_citation_coverage:
        failures.append(
            f"citation_coverage {citation_coverage:.3f} < threshold {min_citation_coverage:.3f}"
        )
    if min_groundedness is not None and groundedness < min_groundedness:
        failures.append(f"groundedness {groundedness:.3f} < threshold {min_groundedness:.3f}")
    if min_retrieval_hit_rate is not None and retrieval_hit_rate < min_retrieval_hit_rate:
        failures.append(
            f"retrieval_hit_rate {retrieval_hit_rate:.3f} < threshold {min_retrieval_hit_rate:.3f}"
        )
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Run golden evaluation dataset checks")
    parser.add_argument(
        "--dataset", default=str(DEFAULT_DATASET), help="Path to golden dataset JSONL"
    )
    parser.add_argument(
        "--results",
        default=None,
        help=(
            "Optional results JSONL. If omitted and --api-base-url is set, "
            "results will be generated via live /v1/ask calls."
        ),
    )
    parser.add_argument(
        "--api-base-url",
        default=None,
        help="Optional API base URL for live eval runner, e.g. http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--output-results",
        default="evals/results.latest.jsonl",
        help="Where to write generated results for live eval runs",
    )
    parser.add_argument(
        "--report-out",
        default="evals/reports/latest_eval_report.json",
        help="Where to write evaluation report JSON",
    )
    parser.add_argument("--top-k", type=int, default=20, help="Top-K retrieval window")
    parser.add_argument("--timeout-s", type=float, default=20.0, help="Live API timeout in seconds")
    parser.add_argument("--min-citation-coverage", type=float, default=None)
    parser.add_argument("--min-groundedness", type=float, default=None)
    parser.add_argument("--min-retrieval-hit-rate", type=float, default=None)
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    dataset_rows = load_jsonl_rows(dataset_path)
    try:
        validate_dataset_rows(dataset_rows)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    dataset_summary = summarize_dataset(dataset_rows)
    print(f"Loaded {len(dataset_rows)} golden queries from {dataset_path}")
    print(f"Answer type coverage: {dataset_summary['answer_type_coverage']}")
    print(f"Difficulty split: {dataset_summary['difficulty_split']}")
    print(f"Language split: {dataset_summary['language_split']}")
    print(f"Expected source-type coverage: {dataset_summary['expected_source_type_coverage']}")

    results_rows: list[dict[str, Any]] | None = None
    llm_runtime_metrics: dict[str, Any] | None = None
    if args.results:
        results_rows = load_jsonl_rows(Path(args.results))
        print(f"Loaded {len(results_rows)} evaluation rows from {args.results}")
    elif args.api_base_url:
        output_results = Path(args.output_results)
        results_rows = _run_live_eval(
            dataset_rows=dataset_rows,
            api_base_url=args.api_base_url,
            top_k=args.top_k,
            timeout_s=args.timeout_s,
            output_results=output_results,
        )
        print(f"Generated {len(results_rows)} evaluation rows to {output_results}")
        llm_runtime_metrics = _fetch_llm_runtime_metrics(
            api_base_url=args.api_base_url,
            timeout_s=args.timeout_s,
        )

    if results_rows is None:
        print(
            "No results to evaluate. Provide --results or --api-base-url. "
            "Dataset schema and coverage are valid."
        )
        return

    metrics, query_diagnostics, failures = compute_metrics(
        dataset_rows=dataset_rows, results_rows=results_rows, top_k=args.top_k
    )
    if failures:
        raise SystemExit("Evaluation failed: " + "; ".join(failures))

    print("Computed metrics:")
    print(f"  citation_coverage: {metrics.citation_coverage:.3f}")
    print(f"  groundedness: {metrics.groundedness:.3f}")
    print(f"  retrieval_hit_rate@{args.top_k}: {metrics.retrieval_hit_rate:.3f}")
    print(f"  cited_source_type_coverage: {metrics.source_type_coverage}")

    threshold_failures = _evaluate_thresholds(
        metrics=metrics.to_dict(),
        min_citation_coverage=args.min_citation_coverage,
        min_groundedness=args.min_groundedness,
        min_retrieval_hit_rate=args.min_retrieval_hit_rate,
    )
    if threshold_failures:
        raise SystemExit("Evaluation thresholds failed: " + "; ".join(threshold_failures))

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_path": str(dataset_path),
        "results_path": args.results or str(Path(args.output_results)),
        "top_k": args.top_k,
        "metrics": metrics.to_dict(),
        "llm_runtime": llm_runtime_metrics,
        "dataset_summary": dataset_summary,
        "query_diagnostics": [item.to_dict() for item in query_diagnostics],
    }
    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote evaluation report to {report_path}")


if __name__ == "__main__":
    main()
