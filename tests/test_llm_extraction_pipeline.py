from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.models import Issue, IssueProperty, IssueStatus, Journal, Project
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.extraction.properties import EXTRACTOR_VERSION, extract_issue_properties


@pytest.fixture
async def isolated_llm_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "llm_extract_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_EXTRACT_ENABLED", "true")
    monkeypatch.setenv("LLM_EXTRACT_MAX_RETRIES", "1")
    monkeypatch.setenv("LLM_EXTRACT_BATCH_SIZE", "10")
    monkeypatch.setenv("LLM_EXTRACT_COST_LIMIT_USD", "10")
    monkeypatch.setenv("LLM_EXTRACT_MAX_CONTEXT_CHARS", "4000")

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


async def _seed_issue(issue_id: int) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(Project(id=1, identifier="platform-core", name="SupportHub Platform"))
        session.add_all(
            [
                IssueStatus(id=1, name="New", is_closed=False, is_default=True),
                IssueStatus(id=2, name="In Progress", is_closed=False, is_default=False),
                IssueStatus(id=5, name="Closed", is_closed=True, is_default=False),
            ]
        )
        session.add(
            Issue(
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
                subject="OAuth callback timeout in incident flow",
                description="Incident command runbook documents rollback and handoff procedure.",
                author_id=1,
                assigned_to_id=10,
                author="Alice",
                assigned_to="Bob",
                start_date=None,
                due_date=None,
                done_ratio=35,
                is_private=False,
                estimated_hours=6.0,
                spent_hours=2.0,
                created_on=_dt(9, 0),
                updated_on=_dt(10, 0),
                closed_on=None,
                custom_fields={},
            )
        )
        session.add(
            Journal(
                id=5001,
                issue_id=issue_id,
                user_id=10,
                author="Bob",
                notes="First response and handoff to incident command. Rollback ready.",
                private_notes=False,
                created_on=_dt(9, 30),
                details={
                    "items": [
                        {
                            "property": "attr",
                            "name": "status_id",
                            "old_value": "1",
                            "new_value": "2",
                        },
                        {
                            "property": "attr",
                            "name": "assigned_to_id",
                            "old_value": "10",
                            "new_value": "11",
                        },
                    ]
                },
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_extract_properties_persists_llm_metadata_when_enabled(isolated_llm_db: None) -> None:
    await _seed_issue(issue_id=701)

    response = await extract_issue_properties([701])
    assert response.accepted is True
    assert response.processed_issues == 1

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = await session.scalar(select(IssueProperty).where(IssueProperty.issue_id == 701))

    assert row is not None
    assert row.extractor_version == f"{EXTRACTOR_VERSION}+llm-json-v1"
    llm = row.props_json["llm"]
    assert llm["status"] == "ok"
    assert llm["extractor_version"] == "llm-json-v1"
    assert llm["prompt_version"] == "extract_properties.v1"
    assert llm["schema_version"] == "extract_properties.schema.v1"
    assert llm["attempts"] >= 1
    assert llm["error_bucket"] is None
    assert llm["properties"] is not None
    assert row.confidence >= 0.0


class _InvalidJsonClient:
    async def extract(
        self,
        *,
        system_prompt: str,
        user_content: str,
        schema: dict[str, object],
        model: str,
        timeout_s: float,
    ) -> str:
        del system_prompt, user_content, schema, model, timeout_s
        return "not valid json"


@pytest.mark.asyncio
async def test_extract_properties_retries_and_buckets_invalid_json(
    isolated_llm_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _seed_issue(issue_id=702)

    from redmine_rag.extraction import properties as properties_module

    monkeypatch.setattr(
        properties_module,
        "build_structured_extraction_client",
        lambda _provider: _InvalidJsonClient(),
    )

    response = await extract_issue_properties([702])
    assert response.accepted is True
    assert response.processed_issues == 1

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = await session.scalar(select(IssueProperty).where(IssueProperty.issue_id == 702))

    assert row is not None
    llm = row.props_json["llm"]
    assert llm["status"] == "failed"
    assert llm["error_bucket"] == "invalid_json"
    assert llm["attempts"] == 2
    assert llm["properties"] is None
    assert row.confidence == 0.0
