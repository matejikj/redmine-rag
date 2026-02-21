from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.models import Issue, IssueMetric, IssueProperty, IssueStatus, Journal, Project
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.extraction.properties import EXTRACTOR_VERSION, extract_issue_properties


@pytest.fixture
async def isolated_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "properties_test.db"
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


def _dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 2, 20, hour, minute, tzinfo=UTC)


async def _seed_statuses_and_project() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(Project(id=1, identifier="platform-core", name="SupportHub Platform"))
        session.add_all(
            [
                IssueStatus(id=1, name="New", is_closed=False, is_default=True),
                IssueStatus(id=2, name="In Progress", is_closed=False, is_default=False),
                IssueStatus(id=3, name="Resolved", is_closed=False, is_default=False),
                IssueStatus(id=4, name="Reopened", is_closed=False, is_default=False),
                IssueStatus(id=5, name="Closed", is_closed=True, is_default=False),
            ]
        )
        await session.commit()


def _issue_row(issue_id: int, *, created_on: datetime, updated_on: datetime) -> Issue:
    return Issue(
        id=issue_id,
        project_id=1,
        tracker="Bug",
        status="In Progress",
        priority="High",
        tracker_id=1,
        status_id=2,
        priority_id=3,
        category_id=None,
        fixed_version_id=None,
        subject=f"Issue {issue_id}",
        description="deterministic extraction fixture",
        author_id=1,
        assigned_to_id=10,
        author="Alice",
        assigned_to="Bob",
        start_date=None,
        due_date=None,
        done_ratio=30,
        is_private=False,
        estimated_hours=4.0,
        spent_hours=1.0,
        created_on=created_on,
        updated_on=updated_on,
        closed_on=None,
        custom_fields={},
    )


@pytest.mark.asyncio
async def test_extract_issue_properties_computes_reopen_and_resolution_metrics(
    isolated_db: None,
) -> None:
    await _seed_statuses_and_project()
    session_factory = get_session_factory()
    created_on = _dt(9, 0)

    async with session_factory() as session:
        session.add(_issue_row(101, created_on=created_on, updated_on=_dt(18, 5)))
        session.add_all(
            [
                Journal(
                    id=1001,
                    issue_id=101,
                    user_id=10,
                    author="Bob",
                    notes="First reaction",
                    private_notes=False,
                    created_on=_dt(9, 30),
                    details={"items": []},
                ),
                Journal(
                    id=1002,
                    issue_id=101,
                    user_id=10,
                    author="Bob",
                    notes="Moved to work in progress",
                    private_notes=False,
                    created_on=_dt(10, 0),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "status_id",
                                "old_value": "1",
                                "new_value": "2",
                            }
                        ]
                    },
                ),
                Journal(
                    id=1003,
                    issue_id=101,
                    user_id=12,
                    author="Carol",
                    notes="Ownership handoff",
                    private_notes=False,
                    created_on=_dt(12, 0),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "assigned_to_id",
                                "old_value": "10",
                                "new_value": "11",
                            }
                        ]
                    },
                ),
                Journal(
                    id=1004,
                    issue_id=101,
                    user_id=11,
                    author="Dan",
                    notes="Closing issue",
                    private_notes=False,
                    created_on=_dt(14, 0),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "status_id",
                                "old_value": "2",
                                "new_value": "5",
                            }
                        ]
                    },
                ),
                Journal(
                    id=1005,
                    issue_id=101,
                    user_id=11,
                    author="Dan",
                    notes="Reopened by customer",
                    private_notes=False,
                    created_on=_dt(16, 0),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "status_id",
                                "old_value": "5",
                                "new_value": "4",
                            }
                        ]
                    },
                ),
                Journal(
                    id=1006,
                    issue_id=101,
                    user_id=11,
                    author="Dan",
                    notes="Closed again",
                    private_notes=False,
                    created_on=_dt(18, 0),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "status_id",
                                "old_value": "4",
                                "new_value": "5",
                            }
                        ]
                    },
                ),
            ]
        )
        await session.commit()

    response = await extract_issue_properties([101])
    assert response.accepted is True
    assert response.processed_issues == 1

    async with session_factory() as session:
        metric = await session.scalar(select(IssueMetric).where(IssueMetric.issue_id == 101))
        props = await session.scalar(select(IssueProperty).where(IssueProperty.issue_id == 101))

    assert metric is not None
    assert metric.first_response_s == 1800
    assert metric.resolution_s == 18000
    assert metric.reopen_count == 1
    assert metric.touch_count == 6
    assert metric.handoff_count == 1

    assert props is not None
    assert props.extractor_version == EXTRACTOR_VERSION
    assert props.confidence == 1.0
    assert props.props_json["status_path"] == [1, 2, 5, 4, 5]
    assert props.props_json["validation"]["anomalies"] == []
    assert props.props_json["validation"]["invalid_status_transition_count"] == 0


@pytest.mark.asyncio
async def test_extract_issue_properties_marks_invalid_transitions_and_timestamp_anomalies(
    isolated_db: None,
) -> None:
    await _seed_statuses_and_project()
    session_factory = get_session_factory()
    created_on = _dt(9, 0)

    async with session_factory() as session:
        session.add(_issue_row(102, created_on=created_on, updated_on=_dt(10, 30)))
        session.add_all(
            [
                Journal(
                    id=2001,
                    issue_id=102,
                    user_id=10,
                    author="Bob",
                    notes="Out-of-order log",
                    private_notes=False,
                    created_on=_dt(8, 55),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "status_id",
                                "old_value": "1",
                                "new_value": "2",
                            }
                        ]
                    },
                ),
                Journal(
                    id=2002,
                    issue_id=102,
                    user_id=10,
                    author="Bob",
                    notes="Chain break",
                    private_notes=False,
                    created_on=_dt(10, 0),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "status_id",
                                "old_value": "4",
                                "new_value": "5",
                            }
                        ]
                    },
                ),
                Journal(
                    id=2003,
                    issue_id=102,
                    user_id=10,
                    author="Bob",
                    notes="Missing new value",
                    private_notes=False,
                    created_on=_dt(10, 30),
                    details={
                        "items": [
                            {
                                "property": "attr",
                                "name": "status_id",
                                "old_value": "5",
                                "new_value": "not-a-number",
                            }
                        ]
                    },
                ),
            ]
        )
        await session.commit()

    response = await extract_issue_properties([102])
    assert response.accepted is True
    assert response.processed_issues == 1

    async with session_factory() as session:
        metric = await session.scalar(select(IssueMetric).where(IssueMetric.issue_id == 102))
        props = await session.scalar(select(IssueProperty).where(IssueProperty.issue_id == 102))

    assert metric is not None
    assert metric.first_response_s == 3600
    assert metric.resolution_s == 3600
    assert metric.reopen_count == 0
    assert metric.touch_count == 3
    assert metric.handoff_count == 0

    assert props is not None
    validation = props.props_json["validation"]
    assert "journal_before_issue_created" in validation["anomalies"]
    assert "status_transition_chain_break" in validation["anomalies"]
    assert "status_transition_missing_value" in validation["anomalies"]
    assert validation["timestamp_anomaly_count"] == 1
    assert validation["invalid_status_transition_count"] >= 2
