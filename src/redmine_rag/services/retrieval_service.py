from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.api.schemas import AskFilters


@dataclass(slots=True)
class RetrievedChunk:
    id: int
    text: str
    url: str
    source_type: str
    source_id: str
    score: float


async def hybrid_retrieve(
    session: AsyncSession,
    query: str,
    filters: AskFilters,
    top_k: int,
) -> list[RetrievedChunk]:
    terms = [term for term in re.split(r"\W+", query.lower()) if term]
    if not terms:
        return []

    match_query = " OR ".join(f'"{term.replace('"', '""')}"' for term in terms)
    where_clauses = ["doc_chunk_fts MATCH :match_query"]
    params: dict[str, object] = {
        "match_query": match_query,
        "limit": max(top_k * 3, top_k),
    }

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
    ORDER BY rank ASC
    LIMIT :limit
    """

    try:
        rows = (await session.execute(text(sql), params)).mappings().all()
    except OperationalError:
        return []

    scored: list[RetrievedChunk] = []
    for row in rows:
        rank = abs(float(row["rank"] or 0.0))
        score = 1.0 / (1.0 + rank)
        updated_on = _parse_db_datetime(row.get("source_updated_on"))
        if updated_on is not None:
            score += _freshness_boost(updated_on)
        scored.append(
            RetrievedChunk(
                id=int(row["id"]),
                text=str(row["text"]),
                url=str(row["url"]),
                source_type=str(row["source_type"]),
                source_id=str(row["source_id"]),
                score=score,
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def _freshness_boost(updated_on: datetime) -> float:
    now = datetime.now(updated_on.tzinfo)
    age_days = max((now - updated_on).days, 0)
    if age_days <= 7:
        return 0.5
    if age_days <= 30:
        return 0.2
    return 0.0


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
