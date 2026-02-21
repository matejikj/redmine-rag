from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.models import Issue, IssueMetric, IssueProperty, Project
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.main import app
from redmine_rag.services.metrics_service import EXTRACTOR_VERSION


@pytest.fixture
async def isolated_metrics_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "metrics_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

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


def _dt(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 2, day, hour, 0, tzinfo=UTC)


def _issue_row(issue_id: int, *, project_id: int, updated_on: datetime) -> Issue:
    return Issue(
        id=issue_id,
        project_id=project_id,
        tracker="Bug",
        status="In Progress",
        priority="Normal",
        tracker_id=1,
        status_id=2,
        priority_id=2,
        category_id=None,
        fixed_version_id=None,
        subject=f"Issue {issue_id}",
        description="metrics summary fixture",
        author_id=1,
        assigned_to_id=2,
        author="Alice",
        assigned_to="Bob",
        start_date=None,
        due_date=None,
        done_ratio=25,
        is_private=False,
        estimated_hours=2.0,
        spent_hours=1.0,
        created_on=_dt(1, 9),
        updated_on=updated_on,
        closed_on=None,
        custom_fields={},
    )


async def _seed_metrics_data() -> None:
    session_factory = get_session_factory()
    extracted_at = _dt(21, 8)
    async with session_factory() as session:
        session.add_all(
            [
                Project(id=1, identifier="platform-core", name="SupportHub Platform"),
                Project(id=2, identifier="ops-core", name="SupportHub Ops"),
                _issue_row(11, project_id=1, updated_on=_dt(10, 12)),
                _issue_row(12, project_id=1, updated_on=_dt(14, 12)),
                _issue_row(21, project_id=2, updated_on=_dt(16, 12)),
                _issue_row(22, project_id=2, updated_on=_dt(16, 12)),
                IssueMetric(
                    issue_id=11,
                    first_response_s=600,
                    resolution_s=7200,
                    reopen_count=1,
                    touch_count=4,
                    handoff_count=1,
                ),
                IssueMetric(
                    issue_id=12,
                    first_response_s=None,
                    resolution_s=None,
                    reopen_count=0,
                    touch_count=2,
                    handoff_count=0,
                ),
                IssueMetric(
                    issue_id=21,
                    first_response_s=1200,
                    resolution_s=10800,
                    reopen_count=2,
                    touch_count=5,
                    handoff_count=2,
                ),
                IssueMetric(
                    issue_id=22,
                    first_response_s=30,
                    resolution_s=60,
                    reopen_count=0,
                    touch_count=1,
                    handoff_count=0,
                ),
                IssueProperty(
                    issue_id=11,
                    extractor_version=EXTRACTOR_VERSION,
                    confidence=1.0,
                    props_json={},
                    extracted_at=extracted_at,
                ),
                IssueProperty(
                    issue_id=12,
                    extractor_version=EXTRACTOR_VERSION,
                    confidence=1.0,
                    props_json={},
                    extracted_at=extracted_at,
                ),
                IssueProperty(
                    issue_id=21,
                    extractor_version=EXTRACTOR_VERSION,
                    confidence=1.0,
                    props_json={},
                    extracted_at=extracted_at,
                ),
                IssueProperty(
                    issue_id=22,
                    extractor_version="legacy-v0",
                    confidence=1.0,
                    props_json={},
                    extracted_at=extracted_at,
                ),
            ]
        )
        await session.commit()


def test_metrics_summary_endpoint_returns_aggregations_by_project(
    isolated_metrics_env: None,
) -> None:
    import asyncio

    asyncio.run(_seed_metrics_data())
    client = TestClient(app)

    response = client.get("/v1/metrics/summary")
    assert response.status_code == 200
    payload = response.json()

    assert payload["extractor_version"] == EXTRACTOR_VERSION
    assert payload["issues_total"] == 3
    assert payload["issues_with_first_response"] == 2
    assert payload["issues_with_resolution"] == 2
    assert payload["avg_first_response_s"] == 900.0
    assert payload["avg_resolution_s"] == 9000.0
    assert payload["reopen_total"] == 3
    assert payload["touch_total"] == 11
    assert payload["handoff_total"] == 3

    assert [row["project_id"] for row in payload["by_project"]] == [1, 2]
    by_project = {row["project_id"]: row for row in payload["by_project"]}
    assert by_project[1]["issues_total"] == 2
    assert by_project[1]["avg_first_response_s"] == 600.0
    assert by_project[2]["issues_total"] == 1
    assert by_project[2]["avg_first_response_s"] == 1200.0


def test_metrics_summary_endpoint_applies_project_and_time_filters(
    isolated_metrics_env: None,
) -> None:
    import asyncio

    asyncio.run(_seed_metrics_data())
    client = TestClient(app)

    response = client.get(
        "/v1/metrics/summary",
        params={
            "project_ids": 1,
            "from_date": "2026-02-01T00:00:00Z",
            "to_date": "2026-02-12T23:59:59Z",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["issues_total"] == 1
    assert payload["issues_with_first_response"] == 1
    assert payload["issues_with_resolution"] == 1
    assert payload["avg_first_response_s"] == 600.0
    assert payload["avg_resolution_s"] == 7200.0
    assert payload["reopen_total"] == 1
    assert payload["touch_total"] == 4
    assert payload["handoff_total"] == 1
    assert len(payload["by_project"]) == 1
    assert payload["by_project"][0]["project_id"] == 1
