from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.models import Issue, Project, RawEntity
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.ingestion.repository import IngestionRepository


@pytest.fixture
async def isolated_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "repo_test.db"
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


@pytest.mark.asyncio
async def test_raw_entity_upsert_is_idempotent(isolated_db: None) -> None:
    fetched_at = datetime.now(UTC)
    session_factory = get_session_factory()

    async with session_factory() as session:
        repo = IngestionRepository(session)
        await repo.upsert_raw_entity(
            {
                "entity_type": "issue",
                "entity_id": "101",
                "endpoint": "/issues.json",
                "project_id": 1,
                "updated_on": fetched_at,
                "fetched_at": fetched_at,
                "payload": {"subject": "before"},
            }
        )
        await repo.upsert_raw_entity(
            {
                "entity_type": "issue",
                "entity_id": "101",
                "endpoint": "/issues.json",
                "project_id": 1,
                "updated_on": fetched_at,
                "fetched_at": fetched_at,
                "payload": {"subject": "after"},
            }
        )
        await session.commit()

    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(RawEntity))
        row = await session.scalar(select(RawEntity))

    assert count == 1
    assert row is not None
    assert row.payload["subject"] == "after"


@pytest.mark.asyncio
async def test_issue_upsert_updates_existing_row(isolated_db: None) -> None:
    fetched_at = datetime.now(UTC)
    session_factory = get_session_factory()

    async with session_factory() as session:
        repo = IngestionRepository(session)
        await repo.upsert_projects(
            [
                {
                    "id": 1,
                    "identifier": "platform-core",
                    "name": "SupportHub Platform",
                    "description": None,
                    "status": 1,
                    "is_public": True,
                    "parent_id": None,
                    "homepage": None,
                    "created_on": fetched_at,
                    "updated_on": fetched_at,
                }
            ]
        )
        await repo.upsert_issues(
            [
                {
                    "id": 42,
                    "project_id": 1,
                    "tracker": "Feature",
                    "status": "New",
                    "priority": "Normal",
                    "tracker_id": 2,
                    "status_id": 1,
                    "priority_id": 2,
                    "category_id": None,
                    "fixed_version_id": None,
                    "subject": "Original subject",
                    "description": "Original description",
                    "author_id": None,
                    "assigned_to_id": None,
                    "author": None,
                    "assigned_to": None,
                    "start_date": None,
                    "due_date": None,
                    "done_ratio": 0,
                    "is_private": False,
                    "estimated_hours": None,
                    "spent_hours": None,
                    "created_on": fetched_at,
                    "updated_on": fetched_at,
                    "closed_on": None,
                    "custom_fields": {},
                }
            ]
        )
        await repo.upsert_issues(
            [
                {
                    "id": 42,
                    "project_id": 1,
                    "tracker": "Feature",
                    "status": "In Progress",
                    "priority": "High",
                    "tracker_id": 2,
                    "status_id": 2,
                    "priority_id": 3,
                    "category_id": None,
                    "fixed_version_id": None,
                    "subject": "Updated subject",
                    "description": "Updated description",
                    "author_id": None,
                    "assigned_to_id": None,
                    "author": None,
                    "assigned_to": None,
                    "start_date": None,
                    "due_date": None,
                    "done_ratio": 20,
                    "is_private": False,
                    "estimated_hours": None,
                    "spent_hours": None,
                    "created_on": fetched_at,
                    "updated_on": fetched_at,
                    "closed_on": None,
                    "custom_fields": {},
                }
            ]
        )
        await session.commit()

    async with session_factory() as session:
        issue_count = await session.scalar(select(func.count()).select_from(Issue))
        issue_row = await session.scalar(select(Issue).where(Issue.id == 42))
        project_count = await session.scalar(select(func.count()).select_from(Project))

    assert project_count == 1
    assert issue_count == 1
    assert issue_row is not None
    assert issue_row.subject == "Updated subject"
    assert issue_row.status == "In Progress"
