from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.services import ops_service
from redmine_rag.services.llm_runtime import LlmRuntimeProbe
from redmine_rag.services.ops_service import (
    create_state_backup,
    get_health_status,
    resolve_sqlite_db_path,
    restore_state_backup,
    run_sqlite_maintenance,
)


@pytest.fixture
def isolated_ops_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "ops.db"
    vector_index = tmp_path / "chunks.index"
    vector_meta = tmp_path / "chunks.meta.json"

    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("VECTOR_INDEX_PATH", str(vector_index))
    monkeypatch.setenv("VECTOR_META_PATH", str(vector_meta))

    get_settings.cache_clear()

    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO test_table (value) VALUES ('seed')")
        conn.commit()
    vector_index.write_bytes(b"vector-index")
    vector_meta.write_text('{"keys":["a"]}', encoding="utf-8")

    yield {
        "db_path": db_path,
        "vector_index": vector_index,
        "vector_meta": vector_meta,
        "tmp_path": tmp_path,
    }

    get_settings.cache_clear()


@pytest.fixture
async def isolated_health_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "health.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("LLM_EXTRACT_ENABLED", "true")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "Mistral-7B-Instruct-v0.3-Q4_K_M")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def test_resolve_sqlite_db_path() -> None:
    path = resolve_sqlite_db_path("sqlite+aiosqlite:///./data/redmine_rag.db")
    assert path.name == "redmine_rag.db"


def test_create_and_restore_backup(isolated_ops_env: dict[str, Path]) -> None:
    backup_root = isolated_ops_env["tmp_path"] / "backups"
    summary = create_state_backup(destination_dir=backup_root)
    backup_dir = Path(summary["backup_dir"])

    assert backup_dir.exists()
    assert (backup_dir / "manifest.json").exists()
    assert (backup_dir / "redmine_rag.db").exists()
    assert (backup_dir / "chunks.index").exists()
    assert (backup_dir / "chunks.meta.json").exists()

    isolated_ops_env["vector_index"].write_bytes(b"changed-index")
    restore_summary = restore_state_backup(source_dir=backup_dir, force=True)
    assert str(isolated_ops_env["vector_index"]) in restore_summary["restored_files"]
    assert isolated_ops_env["vector_index"].read_bytes() == b"vector-index"


def test_restore_requires_force(isolated_ops_env: dict[str, Path]) -> None:
    backup_root = isolated_ops_env["tmp_path"] / "backups"
    summary = create_state_backup(destination_dir=backup_root)
    backup_dir = Path(summary["backup_dir"])

    with pytest.raises(ValueError, match="--force"):
        restore_state_backup(source_dir=backup_dir, force=False)


def test_sqlite_maintenance_runs(isolated_ops_env: dict[str, Path]) -> None:
    summary = run_sqlite_maintenance()
    assert summary["database"].endswith("ops.db")
    assert summary["elapsed_ms"] >= 0


@pytest.mark.asyncio
async def test_health_reports_degraded_when_ollama_runtime_unreachable(
    isolated_health_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _probe_unavailable(*_args, **_kwargs) -> LlmRuntimeProbe:
        return LlmRuntimeProbe(
            provider="ollama",
            base_url="http://127.0.0.1:11434",
            model="Mistral-7B-Instruct-v0.3-Q4_K_M",
            available=False,
            model_available=None,
            detail="Ollama request failed: connection refused",
            latency_ms=12,
        )

    monkeypatch.setattr(ops_service, "probe_llm_runtime", _probe_unavailable)

    response = await get_health_status()
    llm_check = next(check for check in response.checks if check.name == "llm_runtime")

    assert response.status == "degraded"
    assert llm_check.status == "warn"
    assert "connection refused" in (llm_check.detail or "")
