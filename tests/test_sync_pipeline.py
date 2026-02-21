from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.models import (
    DocChunk,
    Issue,
    Journal,
    RawEntity,
    RawIssue,
    RawJournal,
    SyncCursor,
    SyncState,
    TimeEntry,
    WikiPage,
)
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.ingestion.redmine_client import RedmineClient
from redmine_rag.ingestion.sync_pipeline import run_incremental_sync
from redmine_rag.mock_redmine.app import app as mock_redmine_app


@pytest.fixture
async def isolated_sync_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "sync_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("REDMINE_BASE_URL", "http://testserver")
    monkeypatch.setenv("REDMINE_API_KEY", "mock-api-key")
    monkeypatch.setenv("REDMINE_PROJECT_IDS", "1")
    monkeypatch.setenv(
        "REDMINE_MODULES",
        (
            "projects,users,groups,trackers,issue_statuses,issue_priorities,"
            "issues,time_entries,news,documents,files,boards,wiki"
        ),
    )
    monkeypatch.setenv("REDMINE_BOARD_IDS", "94001,94003")
    monkeypatch.setenv(
        "REDMINE_WIKI_PAGES",
        "platform-core:Feature-Login,platform-core:Incident-Triage-Playbook",
    )
    monkeypatch.setenv("SYNC_OVERLAP_MINUTES", "10")

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
async def test_incremental_sync_ingests_mock_redmine_without_duplication(
    isolated_sync_env: None,
) -> None:
    transport = httpx.ASGITransport(app=mock_redmine_app)
    client = RedmineClient(
        base_url="http://testserver",
        api_key="mock-api-key",
        verify_ssl=False,
        transport=transport,
        extra_headers={"X-Mock-Role": "admin"},
    )

    first_summary = await run_incremental_sync(project_ids=[1], client=client)

    assert first_summary["projects_synced"] >= 1
    assert first_summary["issues_synced"] >= 120
    assert first_summary["journals_synced"] >= 120
    assert first_summary["time_entries_synced"] >= 300
    assert first_summary["raw_entities_synced"] > 0
    assert first_summary["wiki_pages_synced"] >= 2
    assert first_summary["chunks_updated"] > 0
    assert first_summary["chunk_sources_reindexed"] > 0

    session_factory = get_session_factory()
    async with session_factory() as session:
        issue_count = await session.scalar(select(func.count()).select_from(Issue))
        journal_count = await session.scalar(select(func.count()).select_from(Journal))
        time_entry_count = await session.scalar(select(func.count()).select_from(TimeEntry))
        raw_issue_count = await session.scalar(select(func.count()).select_from(RawIssue))
        raw_journal_count = await session.scalar(select(func.count()).select_from(RawJournal))
        raw_entity_count = await session.scalar(select(func.count()).select_from(RawEntity))
        wiki_count = await session.scalar(select(func.count()).select_from(WikiPage))
        chunk_count = await session.scalar(select(func.count()).select_from(DocChunk))
        distinct_chunk_keys = await session.scalar(
            select(func.count(func.distinct(DocChunk.embedding_key)))
        )
        state = await session.scalar(
            select(SyncState).where(SyncState.key == "redmine_incremental")
        )
        issues_cursor = await session.scalar(
            select(SyncCursor).where(SyncCursor.entity_type == "issues")
        )
        time_entries_cursor = await session.scalar(
            select(SyncCursor).where(SyncCursor.entity_type == "time_entries")
        )

    assert issue_count is not None
    assert issue_count >= 120
    assert journal_count is not None
    assert journal_count >= 120
    assert time_entry_count is not None
    assert time_entry_count >= 300
    assert raw_issue_count == issue_count
    assert raw_journal_count == journal_count
    assert raw_entity_count is not None
    assert raw_entity_count > 0
    assert wiki_count == 2
    assert chunk_count is not None
    assert chunk_count > 0
    assert distinct_chunk_keys == chunk_count
    assert state is not None
    assert state.last_sync_at is not None
    assert state.last_success_at is not None
    assert state.last_error is None
    assert issues_cursor is not None
    assert issues_cursor.last_seen_updated_on is not None
    assert time_entries_cursor is not None
    assert time_entries_cursor.last_seen_updated_on is not None

    second_summary = await run_incremental_sync(project_ids=[1], client=client)
    assert second_summary["issues_synced"] >= 0

    async with session_factory() as session:
        issue_count_after = await session.scalar(select(func.count()).select_from(Issue))
        journal_count_after = await session.scalar(select(func.count()).select_from(Journal))
        raw_issue_count_after = await session.scalar(select(func.count()).select_from(RawIssue))
        raw_journal_count_after = await session.scalar(select(func.count()).select_from(RawJournal))
        wiki_count_after = await session.scalar(select(func.count()).select_from(WikiPage))
        chunk_count_after = await session.scalar(select(func.count()).select_from(DocChunk))

    assert issue_count_after == issue_count
    assert journal_count_after == journal_count
    assert raw_issue_count_after == raw_issue_count
    assert raw_journal_count_after == raw_journal_count
    assert wiki_count_after == wiki_count
    assert chunk_count_after == chunk_count
