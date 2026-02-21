from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.core.config import get_settings
from redmine_rag.db.models import DocChunk
from redmine_rag.db.session import get_session_factory
from redmine_rag.indexing.embeddings import deterministic_embed_text
from redmine_rag.indexing.vector_store import LocalNumpyVectorStore


@dataclass(slots=True)
class EmbeddingStats:
    processed_chunks: int = 0
    vectors_upserted: int = 0
    removed_vectors: int = 0
    mode: str = "incremental"


class EmbeddingIndexer:
    def __init__(
        self,
        session: AsyncSession,
        store: LocalNumpyVectorStore,
        *,
        embedding_dim: int,
    ) -> None:
        self._session = session
        self._store = store
        self._embedding_dim = embedding_dim

    async def refresh(
        self, *, since: datetime | None, full_rebuild: bool = False
    ) -> EmbeddingStats:
        stats = EmbeddingStats(mode="full_rebuild" if full_rebuild else "incremental")
        await self._ensure_embedding_keys()

        if full_rebuild:
            self._store.clear()
            chunks = (
                (await self._session.execute(select(DocChunk).order_by(DocChunk.id.asc())))
                .scalars()
                .all()
            )
        else:
            stmt = select(DocChunk).order_by(DocChunk.id.asc())
            if since is not None:
                stmt = stmt.where(DocChunk.updated_at >= since)
            chunks = (await self._session.execute(stmt)).scalars().all()

        for chunk in chunks:
            if chunk.embedding_key is None:
                continue
            vector = deterministic_embed_text(chunk.text, dim=self._embedding_dim)
            self._store.upsert(chunk.embedding_key, vector)
            stats.vectors_upserted += 1

        stats.processed_chunks = len(chunks)

        allowed_keys = {
            key
            for key in (await self._session.execute(select(DocChunk.embedding_key))).scalars().all()
            if key
        }
        stats.removed_vectors = self._store.remove_keys_not_in(allowed_keys)
        self._store.save()
        return stats

    async def _ensure_embedding_keys(self) -> None:
        rows = (
            (
                await self._session.execute(
                    select(DocChunk)
                    .where(DocChunk.embedding_key.is_(None))
                    .order_by(DocChunk.id.asc())
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            return

        for row in rows:
            row.embedding_key = _fallback_embedding_key(row.id)
        await self._session.flush()


async def refresh_embeddings(
    *,
    since: datetime | None,
    full_rebuild: bool = False,
) -> dict[str, int | str]:
    settings = get_settings()
    store = LocalNumpyVectorStore(
        index_path=settings.vector_index_path,
        meta_path=settings.vector_meta_path,
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        indexer = EmbeddingIndexer(
            session=session,
            store=store,
            embedding_dim=settings.embedding_dim,
        )
        stats = await indexer.refresh(since=since, full_rebuild=full_rebuild)
        await session.commit()
        return {
            "mode": stats.mode,
            "processed_chunks": stats.processed_chunks,
            "vectors_upserted": stats.vectors_upserted,
            "removed_vectors": stats.removed_vectors,
        }


def _fallback_embedding_key(chunk_id: int) -> str:
    return f"doc_chunk:{chunk_id}"
