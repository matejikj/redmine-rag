from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text

from redmine_rag.api.schemas import AskFilters
from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.models import DocChunk, Issue
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.services.retrieval_service import hybrid_retrieve


@pytest.fixture
async def isolated_retrieval_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "retrieval_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunk_fts
                USING fts5(text, content='doc_chunk', content_rowid='id');
                """
            )
        )
        await connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS doc_chunk_ai AFTER INSERT ON doc_chunk BEGIN
                    INSERT INTO doc_chunk_fts(rowid, text) VALUES (new.id, new.text);
                END;
                """
            )
        )
        await connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS doc_chunk_ad AFTER DELETE ON doc_chunk BEGIN
                    INSERT INTO doc_chunk_fts(doc_chunk_fts, rowid, text)
                    VALUES ('delete', old.id, old.text);
                END;
                """
            )
        )
        await connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS doc_chunk_au AFTER UPDATE ON doc_chunk BEGIN
                    INSERT INTO doc_chunk_fts(doc_chunk_fts, rowid, text)
                    VALUES ('delete', old.id, old.text);
                    INSERT INTO doc_chunk_fts(rowid, text) VALUES (new.id, new.text);
                END;
                """
            )
        )

    yield

    await engine.dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


@pytest.mark.asyncio
async def test_hybrid_retrieve_uses_fts_hits(isolated_retrieval_db: None) -> None:
    now = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                DocChunk(
                    source_type="issue",
                    source_id="101",
                    project_id=1,
                    issue_id=101,
                    chunk_index=0,
                    text="OAuth callback timeout on Safari login flow",
                    url="http://x/issues/101",
                    source_created_on=now,
                    source_updated_on=now,
                    source_metadata={},
                    embedding_key="k101-0",
                ),
                DocChunk(
                    source_type="wiki",
                    source_id="1:Feature-Login",
                    project_id=1,
                    chunk_index=0,
                    text="Runbook for rollback and incident playbook",
                    url="http://x/wiki/Feature-Login",
                    source_created_on=now,
                    source_updated_on=now - timedelta(days=40),
                    source_metadata={},
                    embedding_key="k102-0",
                ),
            ]
        )
        await session.commit()

    async with session_factory() as session:
        results = await hybrid_retrieve(
            session,
            query="OAuth callback",
            filters=AskFilters(),
            top_k=5,
        )

    assert results
    assert results[0].source_type == "issue"
    assert results[0].source_id == "101"


@pytest.mark.asyncio
async def test_hybrid_retrieve_applies_issue_filters(isolated_retrieval_db: None) -> None:
    now = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                Issue(
                    id=201,
                    project_id=1,
                    tracker="Feature",
                    status="New",
                    priority="Normal",
                    tracker_id=2,
                    status_id=1,
                    priority_id=2,
                    category_id=None,
                    fixed_version_id=None,
                    subject="Feature login",
                    description="OAuth enhancement",
                    author_id=None,
                    assigned_to_id=None,
                    author=None,
                    assigned_to=None,
                    start_date=None,
                    due_date=None,
                    done_ratio=0,
                    is_private=False,
                    estimated_hours=None,
                    spent_hours=None,
                    created_on=now,
                    updated_on=now,
                    closed_on=None,
                    custom_fields={},
                ),
                Issue(
                    id=202,
                    project_id=1,
                    tracker="Bug",
                    status="Resolved",
                    priority="High",
                    tracker_id=1,
                    status_id=3,
                    priority_id=3,
                    category_id=None,
                    fixed_version_id=None,
                    subject="Bug login",
                    description="OAuth bug fixed",
                    author_id=None,
                    assigned_to_id=None,
                    author=None,
                    assigned_to=None,
                    start_date=None,
                    due_date=None,
                    done_ratio=100,
                    is_private=False,
                    estimated_hours=None,
                    spent_hours=None,
                    created_on=now,
                    updated_on=now,
                    closed_on=None,
                    custom_fields={},
                ),
                DocChunk(
                    source_type="issue",
                    source_id="201",
                    project_id=1,
                    issue_id=201,
                    chunk_index=0,
                    text="OAuth login rollout plan",
                    url="http://x/issues/201",
                    source_created_on=now,
                    source_updated_on=now,
                    source_metadata={},
                    embedding_key="k201-0",
                ),
                DocChunk(
                    source_type="issue",
                    source_id="202",
                    project_id=1,
                    issue_id=202,
                    chunk_index=0,
                    text="OAuth login rollout plan with bug context",
                    url="http://x/issues/202",
                    source_created_on=now,
                    source_updated_on=now,
                    source_metadata={},
                    embedding_key="k202-0",
                ),
            ]
        )
        await session.commit()

    async with session_factory() as session:
        filtered = await hybrid_retrieve(
            session,
            query="OAuth rollout",
            filters=AskFilters(project_ids=[1], tracker_ids=[2], status_ids=[1]),
            top_k=5,
        )

    assert filtered
    assert all(item.source_id == "201" for item in filtered)
