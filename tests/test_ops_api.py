from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from redmine_rag.core.config import get_settings
from redmine_rag.main import app
from redmine_rag.services.ops_service import reset_ops_run_history


@pytest.fixture
def isolated_ops_api_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "ops_api.db"
    vector_index = tmp_path / "chunks.index"
    vector_meta = tmp_path / "chunks.meta.json"

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("VECTOR_INDEX_PATH", str(vector_index))
    monkeypatch.setenv("VECTOR_META_PATH", str(vector_meta))
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "Mistral-7B-Instruct-v0.3-Q4_K_M")

    get_settings.cache_clear()
    reset_ops_run_history()

    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO test_table (value) VALUES ('seed')")
        conn.commit()
    vector_index.write_bytes(b"index")
    vector_meta.write_text('{"version":1}', encoding="utf-8")

    yield {"tmp_path": tmp_path}

    reset_ops_run_history()
    get_settings.cache_clear()


def test_ops_environment_endpoint_returns_runtime_configuration(
    isolated_ops_api_env: dict[str, Path],
) -> None:
    client = TestClient(app)
    response = client.get("/v1/ops/environment")
    assert response.status_code == 200
    payload = response.json()
    assert payload["app"] == "redmine-rag"
    assert payload["llm_provider"] == "ollama"
    assert payload["llm_model"] == "Mistral-7B-Instruct-v0.3-Q4_K_M"


def test_ops_backup_and_maintenance_endpoints_record_run_history(
    isolated_ops_api_env: dict[str, Path],
) -> None:
    client = TestClient(app)

    backup_response = client.post(
        "/v1/ops/backup",
        json={"output_dir": str(isolated_ops_api_env["tmp_path"] / "backups")},
    )
    assert backup_response.status_code == 200
    backup_payload = backup_response.json()
    assert backup_payload["accepted"] is True
    assert backup_payload["run"]["action"] == "backup"
    assert backup_payload["run"]["status"] == "success"

    maintenance_response = client.post("/v1/ops/maintenance")
    assert maintenance_response.status_code == 200
    maintenance_payload = maintenance_response.json()
    assert maintenance_payload["accepted"] is True
    assert maintenance_payload["run"]["action"] == "maintenance"
    assert maintenance_payload["run"]["status"] == "success"

    runs_response = client.get("/v1/ops/runs", params={"limit": 20})
    assert runs_response.status_code == 200
    runs_payload = runs_response.json()
    assert runs_payload["total"] >= 2
    actions = [item["action"] for item in runs_payload["items"]]
    assert "backup" in actions
    assert "maintenance" in actions
