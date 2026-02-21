from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_DATASET = Path("evals/supporthub_golden_v1.jsonl")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if not rows:
        raise SystemExit(f"Empty JSONL file: {path}")
    return rows


def _normalize_source_key(source: dict[str, Any]) -> str:
    source_type = str(source.get("source_type", "")).strip()
    source_id = source.get("source_id")
    if source_type in {"journal", "attachment"} and "#" in str(source_id):
        return f"{source_type}:{source_id}"
    if source_id is None:
        return f"{source_type}:unknown"
    return f"{source_type}:{source_id}"


def _validate_dataset(rows: list[dict[str, Any]]) -> None:
    if not (40 <= len(rows) <= 80):
        raise SystemExit(f"Expected 40-80 golden queries, got {len(rows)}")

    ids = [str(row.get("id", "")) for row in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("Golden dataset has duplicate query ids")

    for row in rows:
        for field_name in ("id", "query", "expected_answer_type", "expected_sources"):
            if field_name not in row:
                raise SystemExit(f"Dataset row missing field '{field_name}': {row}")
        if not isinstance(row["expected_sources"], list) or not row["expected_sources"]:
            raise SystemExit(f"Query {row['id']} has empty expected_sources")
        for source in row["expected_sources"]:
            if "source_type" not in source:
                raise SystemExit(
                    f"Query {row['id']} has malformed source without source_type: {source}"
                )


def _print_dataset_summary(rows: list[dict[str, Any]]) -> None:
    answer_types = Counter(str(row["expected_answer_type"]) for row in rows)
    difficulties = Counter(str(row.get("difficulty", "unknown")) for row in rows)
    languages = Counter(str(row.get("language", "unknown")) for row in rows)
    source_type_coverage = Counter(
        str(source["source_type"]) for row in rows for source in row["expected_sources"]
    )
    print(f"Loaded {len(rows)} golden queries")
    print(f"Answer type coverage: {dict(answer_types)}")
    print(f"Difficulty split: {dict(difficulties)}")
    print(f"Language split: {dict(languages)}")
    print(f"Expected source-type coverage: {dict(source_type_coverage)}")


def _evaluate_results(
    dataset_rows: list[dict[str, Any]],
    results_rows: list[dict[str, Any]],
    top_k: int,
    min_citation_coverage: float | None,
    min_groundedness: float | None,
    min_retrieval_hit_rate: float | None,
) -> None:
    dataset_by_id = {str(row["id"]): row for row in dataset_rows}
    results_by_id = {str(row.get("id", "")): row for row in results_rows}

    missing_ids = sorted(set(dataset_by_id) - set(results_by_id))
    if missing_ids:
        raise SystemExit(f"Results missing {len(missing_ids)} query ids, e.g. {missing_ids[:5]}")

    citation_scores: list[float] = []
    groundedness_scores: list[float] = []
    retrieval_hits = 0
    source_type_counter: Counter[str] = Counter()

    for query_id, expected in dataset_by_id.items():
        result = results_by_id[query_id]
        claims_total = int(result.get("claims_total", 0))
        claims_with_citation = int(result.get("claims_with_citation", 0))
        claims_grounded = int(result.get("claims_grounded", 0))
        cited_sources = list(result.get("cited_sources", []))
        retrieved_sources = list(result.get("retrieved_sources", []))

        if claims_total > 0:
            citation_coverage = claims_with_citation / claims_total
            groundedness = claims_grounded / claims_total
        else:
            citation_coverage = 1.0 if cited_sources else 0.0
            groundedness = 1.0 if cited_sources else 0.0

        citation_scores.append(citation_coverage)
        groundedness_scores.append(groundedness)
        source_type_counter.update(
            str(source.get("source_type", "unknown")) for source in cited_sources
        )

        expected_keys = {_normalize_source_key(source) for source in expected["expected_sources"]}
        retrieved_keys = [_normalize_source_key(source) for source in retrieved_sources[:top_k]]
        if expected_keys.intersection(retrieved_keys):
            retrieval_hits += 1

    citation_avg = sum(citation_scores) / len(citation_scores)
    groundedness_avg = sum(groundedness_scores) / len(groundedness_scores)
    retrieval_hit_rate = retrieval_hits / len(dataset_by_id)

    print("Computed metrics from results:")
    print(f"  citation_coverage: {citation_avg:.3f}")
    print(f"  groundedness: {groundedness_avg:.3f}")
    print(f"  retrieval_hit_rate@{top_k}: {retrieval_hit_rate:.3f}")
    print(f"  cited_source_type_coverage: {dict(source_type_counter)}")

    failures: list[str] = []
    if min_citation_coverage is not None and citation_avg < min_citation_coverage:
        failures.append(
            f"citation_coverage {citation_avg:.3f} < threshold {min_citation_coverage:.3f}"
        )
    if min_groundedness is not None and groundedness_avg < min_groundedness:
        failures.append(f"groundedness {groundedness_avg:.3f} < threshold {min_groundedness:.3f}")
    if min_retrieval_hit_rate is not None and retrieval_hit_rate < min_retrieval_hit_rate:
        failures.append(
            f"retrieval_hit_rate {retrieval_hit_rate:.3f} < threshold {min_retrieval_hit_rate:.3f}"
        )
    if failures:
        raise SystemExit("Evaluation thresholds failed: " + "; ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run golden evaluation dataset checks")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET),
        help="Path to golden dataset JSONL",
    )
    parser.add_argument(
        "--results",
        default=None,
        help=(
            "Optional results JSONL from /v1/ask evaluation run. "
            "Rows should include id, claims_total, claims_with_citation, claims_grounded, "
            "retrieved_sources[], cited_sources[]."
        ),
    )
    parser.add_argument("--top-k", type=int, default=20, help="Top-K retrieval window")
    parser.add_argument("--min-citation-coverage", type=float, default=None)
    parser.add_argument("--min-groundedness", type=float, default=None)
    parser.add_argument("--min-retrieval-hit-rate", type=float, default=None)
    args = parser.parse_args()

    dataset_rows = _load_jsonl(Path(args.dataset))
    _validate_dataset(dataset_rows)
    _print_dataset_summary(dataset_rows)

    if args.results:
        results_rows = _load_jsonl(Path(args.results))
        _evaluate_results(
            dataset_rows=dataset_rows,
            results_rows=results_rows,
            top_k=args.top_k,
            min_citation_coverage=args.min_citation_coverage,
            min_groundedness=args.min_groundedness,
            min_retrieval_hit_rate=args.min_retrieval_hit_rate,
        )
    else:
        print(
            "No results file provided. Dataset schema and coverage are valid. "
            "Pass --results to compute citation coverage, groundedness, and retrieval hit rate."
        )


if __name__ == "__main__":
    main()
