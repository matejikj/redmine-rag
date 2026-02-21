from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.api.schemas import AskFilters
from redmine_rag.core.config import get_settings
from redmine_rag.indexing.embeddings import deterministic_embed_text
from redmine_rag.indexing.vector_store import LocalNumpyVectorStore


@dataclass(slots=True)
class RetrievedChunk:
    id: int
    text: str
    url: str
    source_type: str
    source_id: str
    score: float
    lexical_rank: int | None = None
    vector_rank: int | None = None
    lexical_score: float | None = None
    vector_score: float | None = None


@dataclass(slots=True)
class RetrievalDiagnostics:
    mode: str
    lexical_candidates: int
    vector_candidates: int
    fused_candidates: int
    lexical_weight: float
    vector_weight: float
    rrf_k: int


@dataclass(slots=True)
class HybridRetrievalResult:
    chunks: list[RetrievedChunk]
    diagnostics: RetrievalDiagnostics


@dataclass(slots=True)
class _ChunkRecord:
    id: int
    text: str
    url: str
    source_type: str
    source_id: str
    updated_on: datetime | None
    lexical_score: float | None = None
    vector_score: float | None = None


def fuse_rankings(
    *,
    lexical_ids: list[int],
    vector_ids: list[int],
    lexical_weight: float,
    vector_weight: float,
    rrf_k: int,
) -> dict[int, float]:
    scores: dict[int, float] = {}
    if lexical_weight > 0:
        for rank, chunk_id in enumerate(lexical_ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + lexical_weight / (rrf_k + rank)
    if vector_weight > 0:
        for rank, chunk_id in enumerate(vector_ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + vector_weight / (rrf_k + rank)
    return scores


async def hybrid_retrieve(
    session: AsyncSession,
    query: str,
    filters: AskFilters,
    top_k: int,
) -> HybridRetrievalResult:
    settings = get_settings()
    candidate_limit = max(top_k * settings.retrieval_candidate_multiplier, top_k)
    lexical = await _retrieve_lexical_candidates(
        session=session,
        query=query,
        filters=filters,
        limit=candidate_limit,
    )

    vector_records = await _retrieve_vector_candidates(
        session=session,
        query=query,
        filters=filters,
        limit=candidate_limit,
        index_path=settings.vector_index_path,
        meta_path=settings.vector_meta_path,
        embedding_dim=settings.embedding_dim,
    )

    lexical_ids = [record.id for record in lexical]
    vector_ids = [record.id for record in vector_records]
    fusion_scores = fuse_rankings(
        lexical_ids=lexical_ids,
        vector_ids=vector_ids,
        lexical_weight=settings.retrieval_lexical_weight,
        vector_weight=settings.retrieval_vector_weight,
        rrf_k=settings.retrieval_rrf_k,
    )

    lexical_by_id = {record.id: record for record in lexical}
    vector_by_id = {record.id: record for record in vector_records}
    chunk_ids = set(fusion_scores)
    if not chunk_ids:
        diagnostics = RetrievalDiagnostics(
            mode="empty",
            lexical_candidates=0,
            vector_candidates=0,
            fused_candidates=0,
            lexical_weight=settings.retrieval_lexical_weight,
            vector_weight=settings.retrieval_vector_weight,
            rrf_k=settings.retrieval_rrf_k,
        )
        return HybridRetrievalResult(chunks=[], diagnostics=diagnostics)

    lexical_rank_map = {chunk_id: rank for rank, chunk_id in enumerate(lexical_ids, start=1)}
    vector_rank_map = {chunk_id: rank for rank, chunk_id in enumerate(vector_ids, start=1)}

    ranked_ids = sorted(
        chunk_ids,
        key=lambda chunk_id: (
            -fusion_scores.get(chunk_id, 0.0),
            lexical_rank_map.get(chunk_id, 10_000),
            vector_rank_map.get(chunk_id, 10_000),
            chunk_id,
        ),
    )

    chunks: list[RetrievedChunk] = []
    for chunk_id in ranked_ids[:top_k]:
        record = lexical_by_id.get(chunk_id) or vector_by_id.get(chunk_id)
        if record is None:
            continue
        score = fusion_scores.get(chunk_id, 0.0)
        if record.updated_on is not None:
            score += _freshness_boost(record.updated_on)
        chunks.append(
            RetrievedChunk(
                id=record.id,
                text=record.text,
                url=record.url,
                source_type=record.source_type,
                source_id=record.source_id,
                score=score,
                lexical_rank=lexical_rank_map.get(chunk_id),
                vector_rank=vector_rank_map.get(chunk_id),
                lexical_score=(lexical_by_id.get(chunk_id) or record).lexical_score,
                vector_score=(vector_by_id.get(chunk_id) or record).vector_score,
            )
        )

    mode = _resolve_mode(lexical_candidates=len(lexical), vector_candidates=len(vector_records))
    diagnostics = RetrievalDiagnostics(
        mode=mode,
        lexical_candidates=len(lexical),
        vector_candidates=len(vector_records),
        fused_candidates=len(chunk_ids),
        lexical_weight=settings.retrieval_lexical_weight,
        vector_weight=settings.retrieval_vector_weight,
        rrf_k=settings.retrieval_rrf_k,
    )
    return HybridRetrievalResult(chunks=chunks, diagnostics=diagnostics)


async def _retrieve_lexical_candidates(
    *,
    session: AsyncSession,
    query: str,
    filters: AskFilters,
    limit: int,
) -> list[_ChunkRecord]:
    terms = [term for term in re.split(r"\W+", query.lower()) if term]
    if not terms:
        return []

    match_query = " OR ".join(f'"{term.replace('"', '""')}"' for term in terms)
    where_clauses = ["doc_chunk_fts MATCH :match_query"]
    params: dict[str, object] = {"match_query": match_query, "limit": limit}
    _append_filter_clauses(where_clauses=where_clauses, params=params, filters=filters)

    sql = f"""
    SELECT
      dc.id,
      dc.text,
      dc.url,
      dc.source_type,
      dc.source_id,
      dc.source_updated_on,
      bm25(doc_chunk_fts) AS rank
    FROM doc_chunk_fts
    JOIN doc_chunk AS dc ON dc.id = doc_chunk_fts.rowid
    LEFT JOIN issue AS i ON i.id = dc.issue_id
    WHERE {" AND ".join(where_clauses)}
    ORDER BY rank ASC, dc.id ASC
    LIMIT :limit
    """

    try:
        rows = (await session.execute(text(sql), params)).mappings().all()
    except OperationalError:
        return []

    output: list[_ChunkRecord] = []
    for row in rows:
        rank = abs(float(row["rank"] or 0.0))
        output.append(
            _ChunkRecord(
                id=int(row["id"]),
                text=str(row["text"]),
                url=str(row["url"]),
                source_type=str(row["source_type"]),
                source_id=str(row["source_id"]),
                updated_on=_parse_db_datetime(row.get("source_updated_on")),
                lexical_score=(1.0 / (1.0 + rank)),
            )
        )
    return output


async def _retrieve_vector_candidates(
    *,
    session: AsyncSession,
    query: str,
    filters: AskFilters,
    limit: int,
    index_path: str,
    meta_path: str,
    embedding_dim: int,
) -> list[_ChunkRecord]:
    store = LocalNumpyVectorStore(index_path=index_path, meta_path=meta_path)
    if not store.keys:
        return []

    query_vector = deterministic_embed_text(query, dim=embedding_dim)
    if not query_vector.any():
        return []

    vector_hits = store.search(query_vector, top_k=limit)
    if not vector_hits:
        return []

    hit_score_map = {hit.key: hit.score for hit in vector_hits}
    where_clauses = []
    params: dict[str, object] = {"limit": limit}

    key_placeholders = []
    for index, key in enumerate(hit_score_map):
        param_key = f"embedding_key_{index}"
        key_placeholders.append(f":{param_key}")
        params[param_key] = key
    where_clauses.append(f"dc.embedding_key IN ({', '.join(key_placeholders)})")
    _append_filter_clauses(where_clauses=where_clauses, params=params, filters=filters)

    sql = f"""
    SELECT
      dc.id,
      dc.embedding_key,
      dc.text,
      dc.url,
      dc.source_type,
      dc.source_id,
      dc.source_updated_on
    FROM doc_chunk AS dc
    LEFT JOIN issue AS i ON i.id = dc.issue_id
    WHERE {" AND ".join(where_clauses)}
    LIMIT :limit
    """
    rows = (await session.execute(text(sql), params)).mappings().all()
    if not rows:
        return []

    records: list[_ChunkRecord] = []
    for row in rows:
        embedding_key = row.get("embedding_key")
        if not isinstance(embedding_key, str):
            continue
        vector_score = hit_score_map.get(embedding_key)
        if vector_score is None:
            continue
        records.append(
            _ChunkRecord(
                id=int(row["id"]),
                text=str(row["text"]),
                url=str(row["url"]),
                source_type=str(row["source_type"]),
                source_id=str(row["source_id"]),
                updated_on=_parse_db_datetime(row.get("source_updated_on")),
                vector_score=vector_score,
            )
        )

    records.sort(key=lambda record: (-float(record.vector_score or 0.0), record.id))
    return records


def _append_filter_clauses(
    *,
    where_clauses: list[str],
    params: dict[str, object],
    filters: AskFilters,
) -> None:
    if filters.project_ids:
        placeholders = []
        for index, project_id in enumerate(filters.project_ids):
            key = f"project_id_{index}"
            placeholders.append(f":{key}")
            params[key] = project_id
        where_clauses.append(f"dc.project_id IN ({', '.join(placeholders)})")

    if filters.from_date is not None:
        where_clauses.append("dc.source_updated_on >= :from_date")
        params["from_date"] = filters.from_date
    if filters.to_date is not None:
        where_clauses.append("dc.source_updated_on <= :to_date")
        params["to_date"] = filters.to_date

    if filters.tracker_ids:
        placeholders = []
        for index, tracker_id in enumerate(filters.tracker_ids):
            key = f"tracker_id_{index}"
            placeholders.append(f":{key}")
            params[key] = tracker_id
        where_clauses.append(f"i.tracker_id IN ({', '.join(placeholders)})")

    if filters.status_ids:
        placeholders = []
        for index, status_id in enumerate(filters.status_ids):
            key = f"status_id_{index}"
            placeholders.append(f":{key}")
            params[key] = status_id
        where_clauses.append(f"i.status_id IN ({', '.join(placeholders)})")


def _freshness_boost(updated_on: datetime) -> float:
    now = datetime.now(updated_on.tzinfo)
    age_days = max((now - updated_on).days, 0)
    if age_days <= 7:
        return 0.5
    if age_days <= 30:
        return 0.2
    return 0.0


def _resolve_mode(*, lexical_candidates: int, vector_candidates: int) -> str:
    if lexical_candidates and vector_candidates:
        return "hybrid"
    if lexical_candidates:
        return "lexical_only"
    if vector_candidates:
        return "vector_only"
    return "empty"


def _parse_db_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        return datetime.fromisoformat(normalized)
    return None
