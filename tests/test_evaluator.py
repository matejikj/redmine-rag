from __future__ import annotations

from redmine_rag.evaluation.evaluator import (
    EvalMetrics,
    compare_metrics,
    compute_metrics,
    normalize_source_key,
)


def test_normalize_source_key_handles_compound_sources() -> None:
    assert (
        normalize_source_key({"source_type": "journal", "source_id": "101#1001"})
        == "journal:101#1001"
    )
    assert normalize_source_key({"source_type": "issue", "source_id": 101}) == "issue:101"
    assert normalize_source_key({"source_type": "wiki", "source_id": None}) == "wiki:unknown"


def test_compute_metrics_returns_expected_values() -> None:
    dataset_rows = [
        {
            "id": "q1",
            "query": "x",
            "expected_answer_type": "summary",
            "expected_sources": [{"source_type": "issue", "source_id": 101}],
        },
        {
            "id": "q2",
            "query": "y",
            "expected_answer_type": "summary",
            "expected_sources": [{"source_type": "wiki", "source_id": "Runbook"}],
        },
    ]
    results_rows = [
        {
            "id": "q1",
            "claims_total": 2,
            "claims_with_citation": 2,
            "claims_grounded": 2,
            "retrieved_sources": [{"source_type": "issue", "source_id": 101}],
            "cited_sources": [{"source_type": "issue", "source_id": 101}],
        },
        {
            "id": "q2",
            "claims_total": 2,
            "claims_with_citation": 1,
            "claims_grounded": 1,
            "retrieved_sources": [{"source_type": "issue", "source_id": 404}],
            "cited_sources": [{"source_type": "issue", "source_id": 404}],
        },
    ]

    metrics, diagnostics, failures = compute_metrics(
        dataset_rows=dataset_rows,
        results_rows=results_rows,
        top_k=20,
    )

    assert failures == []
    assert metrics.query_count == 2
    assert metrics.citation_coverage == 0.75
    assert metrics.groundedness == 0.75
    assert metrics.retrieval_hit_rate == 0.5
    assert metrics.source_type_coverage == {"issue": 2}
    assert len(diagnostics) == 2
    assert diagnostics[0].query_id == "q1"
    assert diagnostics[0].retrieval_hit is True
    assert diagnostics[1].query_id == "q2"
    assert diagnostics[1].retrieval_hit is False


def test_compute_metrics_reports_missing_ids() -> None:
    dataset_rows = [
        {
            "id": "q1",
            "query": "x",
            "expected_answer_type": "summary",
            "expected_sources": [{"source_type": "issue", "source_id": 101}],
        },
        {
            "id": "q2",
            "query": "y",
            "expected_answer_type": "summary",
            "expected_sources": [{"source_type": "wiki", "source_id": "Runbook"}],
        },
    ]
    results_rows = [
        {
            "id": "q1",
            "claims_total": 1,
            "claims_with_citation": 1,
            "claims_grounded": 1,
            "retrieved_sources": [{"source_type": "issue", "source_id": 101}],
            "cited_sources": [{"source_type": "issue", "source_id": 101}],
        }
    ]

    _, diagnostics, failures = compute_metrics(
        dataset_rows=dataset_rows,
        results_rows=results_rows,
        top_k=20,
    )
    assert diagnostics == []
    assert len(failures) == 1
    assert "missing" in failures[0].lower()


def test_compare_metrics_detects_regression() -> None:
    baseline = EvalMetrics(
        query_count=50,
        citation_coverage=0.9,
        groundedness=0.9,
        retrieval_hit_rate=0.8,
        source_type_coverage={},
    )
    current = EvalMetrics(
        query_count=50,
        citation_coverage=0.88,
        groundedness=0.895,
        retrieval_hit_rate=0.75,
        source_type_coverage={},
    )

    comparisons, failures = compare_metrics(
        baseline=baseline,
        current=current,
        allowed_drop={
            "citation_coverage": 0.01,
            "groundedness": 0.01,
            "retrieval_hit_rate": 0.02,
        },
    )

    assert len(comparisons) == 3
    assert len(failures) == 2
    assert "citation_coverage" in failures[0]
    assert "retrieval_hit_rate" in failures[1]
