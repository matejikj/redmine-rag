from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from math import ceil

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.api.schemas import AskFilters
from redmine_rag.core.config import get_settings
from redmine_rag.indexing.embeddings import deterministic_embed_text
from redmine_rag.indexing.vector_store import LocalNumpyVectorStore
from redmine_rag.services.query_planner import build_retrieval_plan

logger = logging.getLogger(__name__)


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
    planner_mode: str = "disabled"
    planner_status: str = "disabled"
    planner_latency_ms: int | None = None
    planner_normalized_query: str | None = None
    planner_expansions: list[str] | None = None
    planner_confidence: float | None = None
    planner_error: str | None = None
    planner_queries: list[str] | None = None
    planner_filters_applied: dict[str, object] | None = None


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
    planner_queries = [query]
    effective_filters = filters
    planner_mode = "disabled"
    planner_status = "disabled"
    planner_latency_ms: int | None = None
    planner_normalized_query: str | None = None
    planner_expansions: list[str] = []
    planner_confidence: float | None = None
    planner_error: str | None = None

    if settings.retrieval_planner_enabled:
        plan, planner_diagnostics = await build_retrieval_plan(
            query=query,
            base_filters=filters,
            settings=settings,
        )
        planner_mode = planner_diagnostics.planner_mode
        planner_status = planner_diagnostics.planner_status
        planner_latency_ms = planner_diagnostics.latency_ms
        planner_normalized_query = planner_diagnostics.normalized_query
        planner_expansions = planner_diagnostics.expansions
        planner_confidence = planner_diagnostics.confidence
        planner_error = planner_diagnostics.error

        if plan is not None:
            effective_filters = await _apply_planner_filters(
                session=session,
                base_filters=filters,
                suggested_filters=plan.suggested_filters,
            )
            planner_queries = _plan_queries(
                original_query=query,
                normalized_query=plan.normalized_query,
                expansions=plan.expansions,
                max_expansions=settings.retrieval_planner_max_expansions,
            )
        logger.info(
            "Retrieval planner completed",
            extra={
                "planner_mode": planner_mode,
                "planner_status": planner_status,
                "planner_latency_ms": planner_latency_ms,
                "planner_normalized_query": planner_normalized_query,
                "planner_expansions": planner_expansions,
                "planner_confidence": planner_confidence,
                "planner_error": planner_error,
                "planner_queries": planner_queries,
            },
        )

    per_query_limit = max(top_k, ceil(candidate_limit / max(len(planner_queries), 1)))
    lexical_all: list[_ChunkRecord] = []
    vector_all: list[_ChunkRecord] = []
    for planner_query in planner_queries:
        lexical_all.extend(
            await _retrieve_lexical_candidates(
                session=session,
                query=planner_query,
                filters=effective_filters,
                limit=per_query_limit,
            )
        )
        vector_all.extend(
            await _retrieve_vector_candidates(
                session=session,
                query=planner_query,
                filters=effective_filters,
                limit=per_query_limit,
                index_path=settings.vector_index_path,
                meta_path=settings.vector_meta_path,
                embedding_dim=settings.embedding_dim,
            )
        )

    lexical = _dedupe_records(records=lexical_all, score_key="lexical_score")
    vector_records = _dedupe_records(records=vector_all, score_key="vector_score")

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
            planner_mode=planner_mode,
            planner_status=planner_status,
            planner_latency_ms=planner_latency_ms,
            planner_normalized_query=planner_normalized_query,
            planner_expansions=planner_expansions,
            planner_confidence=planner_confidence,
            planner_error=planner_error,
            planner_queries=planner_queries,
            planner_filters_applied=_filters_to_diagnostics(effective_filters),
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
        planner_mode=planner_mode,
        planner_status=planner_status,
        planner_latency_ms=planner_latency_ms,
        planner_normalized_query=planner_normalized_query,
        planner_expansions=planner_expansions,
        planner_confidence=planner_confidence,
        planner_error=planner_error,
        planner_queries=planner_queries,
        planner_filters_applied=_filters_to_diagnostics(effective_filters),
    )
    return HybridRetrievalResult(chunks=chunks, diagnostics=diagnostics)


def _plan_queries(
    *,
    original_query: str,
    normalized_query: str,
    expansions: list[str],
    max_expansions: int,
) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for candidate in [normalized_query, original_query]:
        normalized = " ".join(candidate.split()).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    for candidate in expansions[: max(max_expansions, 0)]:
        normalized = " ".join(candidate.split()).strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
    return output or [original_query]


def _dedupe_records(records: list[_ChunkRecord], *, score_key: str) -> list[_ChunkRecord]:
    best: dict[int, _ChunkRecord] = {}
    for record in records:
        current = best.get(record.id)
        if current is None:
            best[record.id] = record
            continue
        current_score = getattr(current, score_key) or 0.0
        new_score = getattr(record, score_key) or 0.0
        if new_score > current_score:
            best[record.id] = record
    output = list(best.values())
    if score_key == "lexical_score":
        output.sort(key=lambda item: (-float(item.lexical_score or 0.0), item.id))
    else:
        output.sort(key=lambda item: (-float(item.vector_score or 0.0), item.id))
    return output


async def _apply_planner_filters(
    *,
    session: AsyncSession,
    base_filters: AskFilters,
    suggested_filters: AskFilters,
) -> AskFilters:
    allowed_projects = await _load_allowed_ids(session, "project")
    allowed_trackers = await _load_allowed_ids(session, "tracker")
    allowed_statuses = await _load_allowed_ids(session, "issue_status")

    suggested_project_ids = [
        item for item in suggested_filters.project_ids if item in allowed_projects
    ]
    suggested_tracker_ids = [
        item for item in suggested_filters.tracker_ids if item in allowed_trackers
    ]
    suggested_status_ids = [
        item for item in suggested_filters.status_ids if item in allowed_statuses
    ]

    return AskFilters(
        project_ids=base_filters.project_ids or suggested_project_ids,
        tracker_ids=base_filters.tracker_ids or suggested_tracker_ids,
        status_ids=base_filters.status_ids or suggested_status_ids,
        from_date=base_filters.from_date or suggested_filters.from_date,
        to_date=base_filters.to_date or suggested_filters.to_date,
    )


async def _load_allowed_ids(session: AsyncSession, table_name: str) -> set[int]:
    try:
        rows = (await session.execute(text(f"SELECT id FROM {table_name}"))).all()
    except OperationalError:
        return set()
    allowed: set[int] = set()
    for row in rows:
        try:
            allowed.add(int(row[0]))
        except (TypeError, ValueError):
            continue
    return allowed


def _filters_to_diagnostics(filters: AskFilters) -> dict[str, object]:
    return {
        "project_ids": list(filters.project_ids),
        "tracker_ids": list(filters.tracker_ids),
        "status_ids": list(filters.status_ids),
        "from_date": filters.from_date.isoformat() if filters.from_date is not None else None,
        "to_date": filters.to_date.isoformat() if filters.to_date is not None else None,
    }


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
