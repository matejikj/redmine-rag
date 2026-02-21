from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from redmine_rag.main import app
from redmine_rag.services import eval_artifacts_service


def test_eval_artifacts_endpoint_returns_missing_state_when_files_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        eval_artifacts_service,
        "_CURRENT_REPORT_PATH",
        tmp_path / "evals" / "reports" / "latest_eval_report.json",
    )
    monkeypatch.setattr(
        eval_artifacts_service,
        "_BASELINE_PATH",
        tmp_path / "evals" / "baseline_metrics.v1.json",
    )
    monkeypatch.setattr(
        eval_artifacts_service,
        "_REGRESSION_GATE_PATH",
        tmp_path / "evals" / "reports" / "latest_regression_gate.json",
    )

    client = TestClient(app)
    response = client.get("/v1/evals/latest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "missing"
    assert payload["current_metrics"] is None
    assert payload["baseline_metrics"] is None
