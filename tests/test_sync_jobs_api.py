from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from redmine_rag.db.base import Base
from redmine_rag.db.models import SyncJob
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.main import app
from redmine_rag.services import sync_service


@pytest.fixture
async def isolated_sync_jobs_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "sync_jobs_api.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

    from redmine_rag.core.config import get_settings

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


async def _seed_sync_jobs() -> None:
    session_factory = get_session_factory()
    now = datetime.now(UTC)
    async with session_factory() as session:
        session.add_all(
            [
                SyncJob(id="job-queued", status="queued", payload={"project_ids": [1]}),
                SyncJob(
                    id="job-running",
                    status="running",
                    payload={"project_ids": [2]},
                    started_at=now,
                ),
                SyncJob(
                    id="job-finished",
                    status="finished",
                    payload={"project_ids": [1], "summary": {"issues_synced": 10}},
                    started_at=now,
                    finished_at=now,
                ),
                SyncJob(
                    id="job-failed",
                    status="failed",
                    payload={"project_ids": [3], "error_type": "ConnectError"},
                    started_at=now,
                    finished_at=now,
                    error_message="network timeout",
                ),
            ]
        )
        await session.commit()


def test_sync_jobs_list_and_detail_endpoints(isolated_sync_jobs_env: None) -> None:
    import asyncio

    asyncio.run(_seed_sync_jobs())
    client = TestClient(app)

    list_response = client.get("/v1/sync/jobs", params={"limit": 10})
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 4
    assert payload["counts"]["queued"] == 1
    assert payload["counts"]["running"] == 1
    assert payload["counts"]["finished"] == 1
    assert payload["counts"]["failed"] == 1
    assert len(payload["items"]) == 4

    failed_response = client.get("/v1/sync/jobs", params={"status": "failed", "limit": 10})
    assert failed_response.status_code == 200
    failed_payload = failed_response.json()
    assert len(failed_payload["items"]) == 1
    assert failed_payload["items"][0]["id"] == "job-failed"

    detail_response = client.get("/v1/sync/jobs/job-finished")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == "job-finished"
    assert detail_payload["status"] == "finished"
    assert "summary" in detail_payload["payload"]

    missing_response = client.get("/v1/sync/jobs/does-not-exist")
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_sync_job_failure_injection_marks_job_failed(
    isolated_sync_jobs_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _raise_connect_error(*_args, **_kwargs):
        request = httpx.Request("GET", "https://redmine.example.com/issues.json")
        raise httpx.ConnectError("simulated network failure", request=request)

    monkeypatch.setattr(sync_service, "run_incremental_sync", _raise_connect_error)

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(SyncJob(id="job-failure-test", status="queued", payload={"project_ids": [1]}))
        await session.commit()

    await sync_service._run_sync_job("job-failure-test")

    async with session_factory() as session:
        row = await session.scalar(select(SyncJob).where(SyncJob.id == "job-failure-test"))

    assert row is not None
    assert row.status == "failed"
    assert row.started_at is not None
    assert row.finished_at is not None
    assert row.error_message is not None
    assert "simulated network failure" in row.error_message
    assert row.payload["error_type"] == "ConnectError"


@pytest.mark.asyncio
async def test_sync_job_passes_module_override_to_pipeline(
    isolated_sync_jobs_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def _fake_incremental_sync(*, project_ids: list[int], modules_override: list[str] | None):
        captured["project_ids"] = project_ids
        captured["modules_override"] = modules_override
        return {"issues_synced": 1, "modules_enabled": modules_override or []}

    monkeypatch.setattr(sync_service, "run_incremental_sync", _fake_incremental_sync)

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            SyncJob(
                id="job-modules-test",
                status="queued",
                payload={"project_ids": [1], "modules": ["issues", "news"]},
            )
        )
        await session.commit()

    await sync_service._run_sync_job("job-modules-test")

    assert captured["project_ids"] == [1]
    assert captured["modules_override"] == ["issues", "news"]

    async with session_factory() as session:
        row = await session.scalar(select(SyncJob).where(SyncJob.id == "job-modules-test"))

    assert row is not None
    assert row.status == "finished"
    assert row.payload["modules"] == ["issues", "news"]
    assert "summary" in row.payload
