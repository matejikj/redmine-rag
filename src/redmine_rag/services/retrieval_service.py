from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.api.schemas import AskFilters
from redmine_rag.db.models import DocChunk


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
    """Baseline hybrid retrieval.

    Current implementation is lexical-only scoring on persisted chunks.
    The interface is intentionally stable so a vector backend can be added
    without changing API handlers.
    """

    stmt: Select[tuple[DocChunk]] = select(DocChunk)

    if filters.project_ids:
        stmt = stmt.where(DocChunk.project_id.in_(filters.project_ids))
    if filters.from_date is not None:
        stmt = stmt.where(DocChunk.source_updated_on >= filters.from_date)
    if filters.to_date is not None:
        stmt = stmt.where(DocChunk.source_updated_on <= filters.to_date)

    try:
        rows = (await session.execute(stmt.limit(500))).scalars().all()
    except OperationalError:
        return []

    terms = [term for term in re.split(r"\s+", query.lower()) if term]
    scored: list[RetrievedChunk] = []

    for row in rows:
        text_lower = row.text.lower()
        score = float(sum(text_lower.count(term) for term in terms))
        if score <= 0:
            continue
        if row.source_updated_on is not None:
            freshness = _freshness_boost(row.source_updated_on)
            score += freshness
        scored.append(
            RetrievedChunk(
                id=row.id,
                text=row.text,
                url=row.url,
                source_type=row.source_type,
                source_id=row.source_id,
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
