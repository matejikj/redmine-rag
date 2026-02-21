from __future__ import annotations

import json
from pathlib import Path

import pytest

from redmine_rag.services import eval_artifacts_service
from redmine_rag.services.eval_artifacts_service import get_eval_artifacts_summary


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


@pytest.mark.asyncio
async def test_eval_artifacts_summary_handles_missing_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = tmp_path / "evals" / "reports" / "latest_eval_report.json"
    baseline = tmp_path / "evals" / "baseline_metrics.v1.json"
    gate = tmp_path / "evals" / "reports" / "latest_regression_gate.json"

    monkeypatch.setattr(eval_artifacts_service, "_CURRENT_REPORT_PATH", current)
    monkeypatch.setattr(eval_artifacts_service, "_BASELINE_PATH", baseline)
    monkeypatch.setattr(eval_artifacts_service, "_REGRESSION_GATE_PATH", gate)

    summary = await get_eval_artifacts_summary()

    assert summary.status == "missing"
    assert summary.current_metrics is None
    assert summary.baseline_metrics is None
    assert summary.comparisons == []
    assert len(summary.notes) == 3


@pytest.mark.asyncio
async def test_eval_artifacts_summary_computes_gate_status_and_deltas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current = tmp_path / "evals" / "reports" / "latest_eval_report.json"
    baseline = tmp_path / "evals" / "baseline_metrics.v1.json"
    gate = tmp_path / "evals" / "reports" / "latest_regression_gate.json"

    _write_json(
        baseline,
        {
            "metrics": {
                "query_count": 50,
                "citation_coverage": 1.0,
                "groundedness": 1.0,
                "retrieval_hit_rate": 1.0,
                "source_type_coverage": {"issue": 44},
            }
        },
    )
    _write_json(
        current,
        {
            "metrics": {
                "query_count": 50,
                "citation_coverage": 0.95,
                "groundedness": 0.99,
                "retrieval_hit_rate": 0.98,
                "source_type_coverage": {"issue": 42},
            }
        },
    )
    _write_json(
        gate,
        {
            "comparisons": [
                {"metric": "citation_coverage", "allowed_drop": 0.01},
                {"metric": "groundedness", "allowed_drop": 0.01},
                {"metric": "retrieval_hit_rate", "allowed_drop": 0.02},
            ],
            "failures": ["citation_coverage dropped too much"],
            "llm_runtime_failures": [],
            "passed": False,
        },
    )

    monkeypatch.setattr(eval_artifacts_service, "_CURRENT_REPORT_PATH", current)
    monkeypatch.setattr(eval_artifacts_service, "_BASELINE_PATH", baseline)
    monkeypatch.setattr(eval_artifacts_service, "_REGRESSION_GATE_PATH", gate)

    summary = await get_eval_artifacts_summary()

    assert summary.status == "fail"
    assert summary.current_metrics is not None
    assert summary.baseline_metrics is not None
    assert len(summary.comparisons) == 3
    assert any(
        item.metric == "citation_coverage" and item.passed is False for item in summary.comparisons
    )
    assert "citation_coverage dropped too much" in summary.failures
