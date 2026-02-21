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
from redmine_rag.indexing.embedding_indexer import refresh_embeddings
from redmine_rag.services import retrieval_service
from redmine_rag.services.query_planner import RetrievalPlan, RetrievalPlanDiagnostics
from redmine_rag.services.retrieval_service import fuse_rankings, hybrid_retrieve


@pytest.fixture
async def isolated_retrieval_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "retrieval_test.db"
    index_path = tmp_path / "retrieval_vectors.index"
    meta_path = tmp_path / "retrieval_vectors.meta.json"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("VECTOR_INDEX_PATH", str(index_path))
    monkeypatch.setenv("VECTOR_META_PATH", str(meta_path))
    monkeypatch.setenv("EMBEDDING_DIM", "128")

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
        retrieval = await hybrid_retrieve(
            session,
            query="OAuth callback",
            filters=AskFilters(),
            top_k=5,
        )

    assert retrieval.chunks
    assert retrieval.chunks[0].source_type == "issue"
    assert retrieval.chunks[0].source_id == "101"
    assert retrieval.diagnostics.mode == "lexical_only"


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

    assert filtered.chunks
    assert all(item.source_id == "201" for item in filtered.chunks)
    assert filtered.diagnostics.mode == "lexical_only"


def test_fuse_rankings_weighted_rrf() -> None:
    scores = fuse_rankings(
        lexical_ids=[10, 11, 12],
        vector_ids=[12, 10],
        lexical_weight=0.6,
        vector_weight=0.4,
        rrf_k=60,
    )
    assert scores[10] > scores[11]
    assert scores[12] > scores[11]
    assert scores[10] != scores[12]


@pytest.mark.asyncio
async def test_hybrid_retrieve_uses_vector_candidates_when_embeddings_exist(
    isolated_retrieval_db: None,
) -> None:
    now = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                DocChunk(
                    source_type="issue",
                    source_id="501",
                    project_id=1,
                    issue_id=501,
                    chunk_index=0,
                    text="payment callback timeout and oauth handoff sequence",
                    url="http://x/issues/501",
                    source_created_on=now,
                    source_updated_on=now,
                    source_metadata={},
                    embedding_key="vec-501",
                ),
                DocChunk(
                    source_type="issue",
                    source_id="502",
                    project_id=1,
                    issue_id=502,
                    chunk_index=0,
                    text="sla escalation war room incident report",
                    url="http://x/issues/502",
                    source_created_on=now,
                    source_updated_on=now,
                    source_metadata={},
                    embedding_key="vec-502",
                ),
            ]
        )
        await session.commit()

    await refresh_embeddings(since=None, full_rebuild=True)

    async with session_factory() as session:
        first = await hybrid_retrieve(
            session,
            query="oauth callback timeout",
            filters=AskFilters(project_ids=[1]),
            top_k=5,
        )
        second = await hybrid_retrieve(
            session,
            query="oauth callback timeout",
            filters=AskFilters(project_ids=[1]),
            top_k=5,
        )

    assert first.diagnostics.mode == "hybrid"
    assert first.diagnostics.vector_candidates > 0
    assert first.chunks
    assert [item.id for item in first.chunks] == [item.id for item in second.chunks]


@pytest.mark.asyncio
async def test_hybrid_retrieve_applies_planner_expansions_and_sanitizes_filters(
    isolated_retrieval_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RETRIEVAL_PLANNER_ENABLED", "true")
    get_settings.cache_clear()

    async def _fake_plan(*_args, **_kwargs):
        return (
            RetrievalPlan(
                normalized_query="idp handshake",
                expansions=["single sign on federation"],
                suggested_filters=AskFilters(
                    project_ids=[999], tracker_ids=[999], status_ids=[999]
                ),
                confidence=0.8,
            ),
            RetrievalPlanDiagnostics(
                planner_mode="llm",
                planner_status="applied",
                latency_ms=12,
                normalized_query="idp handshake",
                expansions=["single sign on federation"],
                confidence=0.8,
            ),
        )

    monkeypatch.setattr(retrieval_service, "build_retrieval_plan", _fake_plan)

    now = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            DocChunk(
                source_type="issue",
                source_id="901",
                project_id=1,
                issue_id=901,
                chunk_index=0,
                text="single sign on federation outage follow-up",
                url="http://x/issues/901",
                source_created_on=now,
                source_updated_on=now,
                source_metadata={},
                embedding_key="planner-901",
            )
        )
        await session.commit()

    async with session_factory() as session:
        retrieval = await hybrid_retrieve(
            session,
            query="idp handshake",
            filters=AskFilters(),
            top_k=5,
        )

    assert retrieval.chunks
    assert retrieval.chunks[0].source_id == "901"
    assert retrieval.diagnostics.planner_status == "applied"
    assert retrieval.diagnostics.planner_queries is not None
    assert "single sign on federation" in retrieval.diagnostics.planner_queries
    applied_filters = retrieval.diagnostics.planner_filters_applied or {}
    assert applied_filters.get("project_ids") == []

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_hybrid_retrieve_falls_back_when_planner_fails(
    isolated_retrieval_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RETRIEVAL_PLANNER_ENABLED", "true")
    get_settings.cache_clear()

    async def _failed_plan(*_args, **_kwargs):
        return (
            None,
            RetrievalPlanDiagnostics(
                planner_mode="llm",
                planner_status="failed",
                latency_ms=7,
                normalized_query=None,
                expansions=[],
                confidence=None,
                error="planner error",
            ),
        )

    monkeypatch.setattr(retrieval_service, "build_retrieval_plan", _failed_plan)

    now = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            DocChunk(
                source_type="issue",
                source_id="902",
                project_id=1,
                issue_id=902,
                chunk_index=0,
                text="callback timeout recovery procedure",
                url="http://x/issues/902",
                source_created_on=now,
                source_updated_on=now,
                source_metadata={},
                embedding_key="planner-902",
            )
        )
        await session.commit()

    async with session_factory() as session:
        retrieval = await hybrid_retrieve(
            session,
            query="callback timeout",
            filters=AskFilters(),
            top_k=5,
        )

    assert retrieval.chunks
    assert retrieval.diagnostics.planner_status == "failed"
    assert retrieval.diagnostics.planner_error == "planner error"
    assert retrieval.diagnostics.planner_queries == ["callback timeout"]

    get_settings.cache_clear()
