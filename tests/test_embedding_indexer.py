from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import delete

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.models import DocChunk
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.indexing.embedding_indexer import refresh_embeddings
from redmine_rag.indexing.vector_store import LocalNumpyVectorStore


@pytest.fixture
async def isolated_embedding_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "embedding_test.db"
    index_path = tmp_path / "chunks.index"
    meta_path = tmp_path / "chunks.meta.json"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("VECTOR_INDEX_PATH", str(index_path))
    monkeypatch.setenv("VECTOR_META_PATH", str(meta_path))
    monkeypatch.setenv("EMBEDDING_DIM", "64")

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
async def test_embedding_indexer_refresh_and_reindex(isolated_embedding_env: None) -> None:
    now = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                DocChunk(
                    source_type="issue",
                    source_id="1001",
                    project_id=1,
                    issue_id=1001,
                    chunk_index=0,
                    text="OAuth callback timeout diagnostic notes",
                    url="http://x/issues/1001",
                    source_created_on=now,
                    source_updated_on=now,
                    source_metadata={},
                    embedding_key="e-1001",
                ),
                DocChunk(
                    source_type="wiki",
                    source_id="1:Feature-Login",
                    project_id=1,
                    chunk_index=0,
                    text="Rollback runbook and mitigation workflow",
                    url="http://x/wiki/Feature-Login",
                    source_created_on=now,
                    source_updated_on=now,
                    source_metadata={},
                    embedding_key="e-1002",
                ),
            ]
        )
        await session.commit()

    full_summary = await refresh_embeddings(since=None, full_rebuild=True)
    assert full_summary["mode"] == "full_rebuild"
    assert full_summary["vectors_upserted"] == 2

    settings = get_settings()
    store = LocalNumpyVectorStore(
        index_path=settings.vector_index_path,
        meta_path=settings.vector_meta_path,
    )
    assert len(store.keys) == 2

    incremental_summary = await refresh_embeddings(
        since=datetime.now(UTC) + timedelta(days=1),
        full_rebuild=False,
    )
    assert incremental_summary["mode"] == "incremental"
    assert incremental_summary["processed_chunks"] == 0

    async with session_factory() as session:
        await session.execute(delete(DocChunk).where(DocChunk.embedding_key == "e-1002"))
        await session.commit()

    cleanup_summary = await refresh_embeddings(since=None, full_rebuild=False)
    assert cleanup_summary["removed_vectors"] >= 1

    store_reloaded = LocalNumpyVectorStore(
        index_path=settings.vector_index_path,
        meta_path=settings.vector_meta_path,
    )
    assert "e-1002" not in set(store_reloaded.keys)
    assert "e-1001" in set(store_reloaded.keys)
