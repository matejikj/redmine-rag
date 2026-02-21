from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvalMetrics:
    query_count: int
    citation_coverage: float
    groundedness: float
    retrieval_hit_rate: float
    source_type_coverage: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvalQueryDiagnostics:
    query_id: str
    citation_coverage: float
    groundedness: float
    retrieval_hit: bool
    expected_sources_total: int
    retrieved_sources_top_k: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RegressionComparison:
    metric: str
    baseline: float
    current: float
    delta: float
    allowed_drop: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"Missing file: {path}")
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if not rows:
        raise ValueError(f"Empty JSONL file: {path}")
    return rows


def normalize_source_key(source: dict[str, Any]) -> str:
    source_type = str(source.get("source_type", "")).strip()
    source_id = source.get("source_id")
    if source_type in {"journal", "attachment"} and "#" in str(source_id):
        return f"{source_type}:{source_id}"
    if source_id is None:
        return f"{source_type}:unknown"
    return f"{source_type}:{source_id}"


def validate_dataset_rows(rows: list[dict[str, Any]]) -> None:
    if not (40 <= len(rows) <= 80):
        raise ValueError(f"Expected 40-80 golden queries, got {len(rows)}")

    ids = [str(row.get("id", "")) for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Golden dataset has duplicate query ids")

    for row in rows:
        for field_name in ("id", "query", "expected_answer_type", "expected_sources"):
            if field_name not in row:
                raise ValueError(f"Dataset row missing field '{field_name}': {row}")
        if not isinstance(row["expected_sources"], list) or not row["expected_sources"]:
            raise ValueError(f"Query {row['id']} has empty expected_sources")
        for source in row["expected_sources"]:
            if "source_type" not in source:
                raise ValueError(
                    f"Query {row['id']} has malformed source without source_type: {source}"
                )


def summarize_dataset(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    answer_types = Counter(str(row["expected_answer_type"]) for row in rows)
    difficulties = Counter(str(row.get("difficulty", "unknown")) for row in rows)
    languages = Counter(str(row.get("language", "unknown")) for row in rows)
    source_type_coverage = Counter(
        str(source["source_type"]) for row in rows for source in row["expected_sources"]
    )
    return {
        "answer_type_coverage": dict(answer_types),
        "difficulty_split": dict(difficulties),
        "language_split": dict(languages),
        "expected_source_type_coverage": dict(source_type_coverage),
    }


def compute_metrics(
    *,
    dataset_rows: list[dict[str, Any]],
    results_rows: list[dict[str, Any]],
    top_k: int,
) -> tuple[EvalMetrics, list[EvalQueryDiagnostics], list[str]]:
    dataset_by_id = {str(row["id"]): row for row in dataset_rows}
    results_by_id = {str(row.get("id", "")): row for row in results_rows}

    failures: list[str] = []
    missing_ids = sorted(set(dataset_by_id) - set(results_by_id))
    if missing_ids:
        failures.append(f"Results missing {len(missing_ids)} query ids, e.g. {missing_ids[:5]}")
        return (
            EvalMetrics(
                query_count=len(dataset_by_id),
                citation_coverage=0.0,
                groundedness=0.0,
                retrieval_hit_rate=0.0,
                source_type_coverage={},
            ),
            [],
            failures,
        )

    citation_scores: list[float] = []
    groundedness_scores: list[float] = []
    retrieval_hits = 0
    source_type_counter: Counter[str] = Counter()
    diagnostics: list[EvalQueryDiagnostics] = []

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

        expected_keys = {normalize_source_key(source) for source in expected["expected_sources"]}
        retrieved_keys = [normalize_source_key(source) for source in retrieved_sources[:top_k]]
        hit = bool(expected_keys.intersection(retrieved_keys))
        if hit:
            retrieval_hits += 1
        diagnostics.append(
            EvalQueryDiagnostics(
                query_id=query_id,
                citation_coverage=citation_coverage,
                groundedness=groundedness,
                retrieval_hit=hit,
                expected_sources_total=len(expected_keys),
                retrieved_sources_top_k=len(retrieved_keys),
            )
        )

    metrics = EvalMetrics(
        query_count=len(dataset_by_id),
        citation_coverage=(sum(citation_scores) / len(citation_scores)),
        groundedness=(sum(groundedness_scores) / len(groundedness_scores)),
        retrieval_hit_rate=(retrieval_hits / len(dataset_by_id)),
        source_type_coverage=dict(source_type_counter),
    )
    return metrics, diagnostics, failures


def compare_metrics(
    *,
    baseline: EvalMetrics,
    current: EvalMetrics,
    allowed_drop: dict[str, float],
) -> tuple[list[RegressionComparison], list[str]]:
    comparisons: list[RegressionComparison] = []
    failures: list[str] = []
    metric_values = {
        "citation_coverage": (baseline.citation_coverage, current.citation_coverage),
        "groundedness": (baseline.groundedness, current.groundedness),
        "retrieval_hit_rate": (baseline.retrieval_hit_rate, current.retrieval_hit_rate),
    }
    for metric_name, (baseline_value, current_value) in metric_values.items():
        max_drop = allowed_drop.get(metric_name, 0.0)
        delta = current_value - baseline_value
        passed = delta >= -max_drop
        comparisons.append(
            RegressionComparison(
                metric=metric_name,
                baseline=baseline_value,
                current=current_value,
                delta=delta,
                allowed_drop=max_drop,
                passed=passed,
            )
        )
        if not passed:
            failures.append(
                f"{metric_name}: current={current_value:.3f}, baseline={baseline_value:.3f}, "
                f"delta={delta:.3f}, allowed_drop={max_drop:.3f}"
            )
    return comparisons, failures
