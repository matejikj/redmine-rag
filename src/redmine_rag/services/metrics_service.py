from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.api.schemas import MetricsSummaryByProject, MetricsSummaryResponse
from redmine_rag.db.models import Issue, IssueMetric, IssueProperty
from redmine_rag.db.session import get_session_factory

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "det-v1"


async def get_metrics_summary(
    *,
    project_ids: list[int],
    from_date: datetime | None,
    to_date: datetime | None,
) -> MetricsSummaryResponse:
    session_factory = get_session_factory()
    async with session_factory() as session:
        totals = await _aggregate_totals(
            session=session,
            project_ids=project_ids,
            from_date=from_date,
            to_date=to_date,
        )
        by_project_rows = await _aggregate_by_project(
            session=session,
            project_ids=project_ids,
            from_date=from_date,
            to_date=to_date,
        )

    summary = MetricsSummaryResponse(
        generated_at=datetime.now(UTC),
        from_date=from_date,
        to_date=to_date,
        project_ids=project_ids,
        extractor_version=EXTRACTOR_VERSION,
        issues_total=_to_int(totals.get("issues_total")),
        issues_with_first_response=_to_int(totals.get("issues_with_first_response")),
        issues_with_resolution=_to_int(totals.get("issues_with_resolution")),
        avg_first_response_s=_to_float_or_none(totals.get("avg_first_response_s")),
        avg_resolution_s=_to_float_or_none(totals.get("avg_resolution_s")),
        reopen_total=_to_int(totals.get("reopen_total")),
        touch_total=_to_int(totals.get("touch_total")),
        handoff_total=_to_int(totals.get("handoff_total")),
        by_project=[
            MetricsSummaryByProject(
                project_id=_to_int(row.get("project_id")),
                issues_total=_to_int(row.get("issues_total")),
                issues_with_first_response=_to_int(row.get("issues_with_first_response")),
                issues_with_resolution=_to_int(row.get("issues_with_resolution")),
                avg_first_response_s=_to_float_or_none(row["avg_first_response_s"]),
                avg_resolution_s=_to_float_or_none(row["avg_resolution_s"]),
                reopen_total=_to_int(row.get("reopen_total")),
                touch_total=_to_int(row.get("touch_total")),
                handoff_total=_to_int(row.get("handoff_total")),
            )
            for row in by_project_rows
        ],
    )
    logger.info(
        "Metrics summary generated",
        extra={
            "project_ids": project_ids,
            "from_date": from_date.isoformat() if from_date is not None else None,
            "to_date": to_date.isoformat() if to_date is not None else None,
            "issues_total": summary.issues_total,
            "by_project_count": len(summary.by_project),
            "extractor_version": EXTRACTOR_VERSION,
        },
    )
    return summary


async def _aggregate_metrics(
    *,
    session: AsyncSession,
    project_ids: list[int],
    from_date: datetime | None,
    to_date: datetime | None,
) -> dict[str, object]:
    stmt = (
        select(
            func.count(Issue.id).label("issues_total"),
            func.sum(case((IssueMetric.first_response_s.is_not(None), 1), else_=0)).label(
                "issues_with_first_response"
            ),
            func.sum(case((IssueMetric.resolution_s.is_not(None), 1), else_=0)).label(
                "issues_with_resolution"
            ),
            func.avg(IssueMetric.first_response_s).label("avg_first_response_s"),
            func.avg(IssueMetric.resolution_s).label("avg_resolution_s"),
            func.coalesce(func.sum(IssueMetric.reopen_count), 0).label("reopen_total"),
            func.coalesce(func.sum(IssueMetric.touch_count), 0).label("touch_total"),
            func.coalesce(func.sum(IssueMetric.handoff_count), 0).label("handoff_total"),
        )
        .select_from(Issue)
        .join(IssueMetric, IssueMetric.issue_id == Issue.id)
        .join(IssueProperty, IssueProperty.issue_id == Issue.id)
        .where(IssueProperty.extractor_version.like(f"{EXTRACTOR_VERSION}%"))
    )

    if project_ids:
        stmt = stmt.where(Issue.project_id.in_(project_ids))
    if from_date is not None:
        stmt = stmt.where(Issue.updated_on >= from_date)
    if to_date is not None:
        stmt = stmt.where(Issue.updated_on <= to_date)

    row = (await session.execute(stmt)).mappings().one()
    return dict(row)


async def _aggregate_by_project(
    *,
    session: AsyncSession,
    project_ids: list[int],
    from_date: datetime | None,
    to_date: datetime | None,
) -> list[dict[str, object]]:
    columns = [
        func.count(Issue.id).label("issues_total"),
        func.sum(case((IssueMetric.first_response_s.is_not(None), 1), else_=0)).label(
            "issues_with_first_response"
        ),
        func.sum(case((IssueMetric.resolution_s.is_not(None), 1), else_=0)).label(
            "issues_with_resolution"
        ),
        func.avg(IssueMetric.first_response_s).label("avg_first_response_s"),
        func.avg(IssueMetric.resolution_s).label("avg_resolution_s"),
        func.coalesce(func.sum(IssueMetric.reopen_count), 0).label("reopen_total"),
        func.coalesce(func.sum(IssueMetric.touch_count), 0).label("touch_total"),
        func.coalesce(func.sum(IssueMetric.handoff_count), 0).label("handoff_total"),
    ]
    columns.insert(0, Issue.project_id.label("project_id"))

    stmt = (
        select(*columns)
        .select_from(Issue)
        .join(IssueMetric, IssueMetric.issue_id == Issue.id)
        .join(IssueProperty, IssueProperty.issue_id == Issue.id)
        .where(IssueProperty.extractor_version.like(f"{EXTRACTOR_VERSION}%"))
    )

    if project_ids:
        stmt = stmt.where(Issue.project_id.in_(project_ids))
    if from_date is not None:
        stmt = stmt.where(Issue.updated_on >= from_date)
    if to_date is not None:
        stmt = stmt.where(Issue.updated_on <= to_date)

    rows = (
        (await session.execute(stmt.group_by(Issue.project_id).order_by(Issue.project_id.asc())))
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


async def _aggregate_totals(
    *,
    session: AsyncSession,
    project_ids: list[int],
    from_date: datetime | None,
    to_date: datetime | None,
) -> dict[str, object]:
    return await _aggregate_metrics(
        session=session,
        project_ids=project_ids,
        from_date=from_date,
        to_date=to_date,
    )


def _to_float_or_none(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _to_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0
        try:
            return int(stripped)
        except ValueError:
            return 0
    return 0
