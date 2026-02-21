from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import BackgroundTasks
from sqlalchemy import select

from redmine_rag.api.schemas import SyncRequest, SyncResponse
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
                payload={"project_ids": payload.project_ids or []},
            )
        )
        await session.commit()

    background_tasks.add_task(_run_sync_job, job_id)

    return SyncResponse(job_id=job_id, accepted=True, detail="Sync job queued")


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

        try:
            project_ids = list(job.payload.get("project_ids", []))
            summary = await run_incremental_sync(project_ids=project_ids)
            job.status = "finished"
            job.finished_at = datetime.now(UTC)
            job.payload = {**job.payload, "summary": summary}
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.finished_at = datetime.now(UTC)
            job.error_message = str(exc)
            await session.commit()
            logger.exception("Sync job failed", extra={"job_id": job_id})
