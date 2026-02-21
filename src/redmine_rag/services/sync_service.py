from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import BackgroundTasks
from sqlalchemy import func, select

from redmine_rag.api.schemas import (
    SyncJobCounts,
    SyncJobListResponse,
    SyncJobResponse,
    SyncRequest,
    SyncResponse,
)
from redmine_rag.core.config import get_settings
from redmine_rag.db.models import SyncJob
from redmine_rag.db.session import get_session_factory
from redmine_rag.ingestion.sync_pipeline import run_incremental_sync

logger = logging.getLogger(__name__)


async def queue_sync_job(payload: SyncRequest, background_tasks: BackgroundTasks) -> SyncResponse:
    job_id = uuid4().hex
    session_factory = get_session_factory()

    async with session_factory() as session:
        session.add(
            SyncJob(
                id=job_id,
                status="queued",
                payload={
                    "project_ids": payload.project_ids or [],
                    "modules": payload.modules,
                },
            )
        )
        await session.commit()

    background_tasks.add_task(_run_sync_job, job_id)
    logger.info(
        "Sync job queued",
        extra={
            "job_id": job_id,
            "project_ids": payload.project_ids or [],
            "modules": payload.modules,
        },
    )

    return SyncResponse(job_id=job_id, accepted=True, detail="Sync job queued")


async def get_sync_job(job_id: str) -> SyncJobResponse | None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        job = await session.scalar(select(SyncJob).where(SyncJob.id == job_id))
        if job is None:
            return None
        return _to_sync_job_response(job)


async def list_sync_jobs(
    *,
    limit: int,
    status: str | None,
) -> SyncJobListResponse:
    settings = get_settings()
    safe_limit = max(1, min(limit, settings.sync_job_history_limit))
    session_factory = get_session_factory()
    async with session_factory() as session:
        stmt = (
            select(SyncJob).order_by(SyncJob.created_at.desc(), SyncJob.id.desc()).limit(safe_limit)
        )
        if status:
            stmt = stmt.where(SyncJob.status == status)
        jobs = list((await session.scalars(stmt)).all())

        count_stmt = select(SyncJob.status, func.count(SyncJob.id)).group_by(SyncJob.status)
        count_rows = (await session.execute(count_stmt)).all()
        counts = SyncJobCounts()
        for row_status, count in count_rows:
            normalized_status = str(row_status).strip().lower()
            if normalized_status == "queued":
                counts.queued = int(count)
            elif normalized_status == "running":
                counts.running = int(count)
            elif normalized_status == "finished":
                counts.finished = int(count)
            elif normalized_status == "failed":
                counts.failed = int(count)

        total = int((await session.scalar(select(func.count(SyncJob.id)))) or 0)
        return SyncJobListResponse(
            items=[_to_sync_job_response(job) for job in jobs],
            total=total,
            counts=counts,
        )


async def _run_sync_job(job_id: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        job = await session.scalar(select(SyncJob).where(SyncJob.id == job_id))
        if job is None:
            logger.error("Sync job not found", extra={"job_id": job_id})
            return

        job.status = "running"
        job.started_at = datetime.now(UTC)
        await session.commit()
        logger.info("Sync job started", extra={"job_id": job_id})

        try:
            project_ids = list(job.payload.get("project_ids", []))
            raw_modules = job.payload.get("modules")
            modules = (
                [str(module) for module in raw_modules] if isinstance(raw_modules, list) else None
            )
            summary = await run_incremental_sync(project_ids=project_ids, modules_override=modules)
            job.status = "finished"
            job.finished_at = datetime.now(UTC)
            job.payload = {**job.payload, "summary": summary}
            await session.commit()
            logger.info(
                "Sync job finished",
                extra={"job_id": job_id, "project_ids": project_ids},
            )
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.finished_at = datetime.now(UTC)
            job.error_message = str(exc)
            job.payload = {**job.payload, "error_type": type(exc).__name__}
            await session.commit()
            logger.exception("Sync job failed", extra={"job_id": job_id})


def _to_sync_job_response(job: SyncJob) -> SyncJobResponse:
    return SyncJobResponse(
        id=job.id,
        status=job.status,
        payload=job.payload,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
