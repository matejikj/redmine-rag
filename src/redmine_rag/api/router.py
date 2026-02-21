from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from redmine_rag.api.schemas import (
    AskRequest,
    AskResponse,
    EvalArtifactsResponse,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    MetricsSummaryResponse,
    OpsActionResponse,
    OpsBackupRequest,
    OpsEnvironmentResponse,
    OpsRunListResponse,
    SyncJobListResponse,
    SyncJobResponse,
    SyncRequest,
    SyncResponse,
)
from redmine_rag.extraction.properties import extract_issue_properties
from redmine_rag.services.ask_service import answer_question
from redmine_rag.services.eval_artifacts_service import get_eval_artifacts_summary
from redmine_rag.services.metrics_service import get_metrics_summary
from redmine_rag.services.ops_service import (
    get_health_status,
    get_ops_environment,
    list_ops_runs,
    run_backup_operation,
    run_maintenance_operation,
)
from redmine_rag.services.sync_service import get_sync_job, list_sync_jobs, queue_sync_job

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return await get_health_status()


@router.post("/v1/ask", response_model=AskResponse)
async def ask(payload: AskRequest) -> AskResponse:
    return await answer_question(payload)


@router.post("/v1/sync/redmine", response_model=SyncResponse)
async def sync_redmine(payload: SyncRequest, background_tasks: BackgroundTasks) -> SyncResponse:
    return await queue_sync_job(payload, background_tasks)


@router.get("/v1/sync/jobs/{job_id}", response_model=SyncJobResponse)
async def sync_job(job_id: str) -> SyncJobResponse:
    job = await get_sync_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Sync job {job_id} was not found")
    return job


@router.get("/v1/sync/jobs", response_model=SyncJobListResponse)
async def sync_jobs(
    limit: int = Query(default=20, ge=1, le=200),
    status: str | None = Query(default=None, pattern="^(queued|running|finished|failed)$"),
) -> SyncJobListResponse:
    return await list_sync_jobs(limit=limit, status=status)


@router.post("/v1/extract/properties", response_model=ExtractResponse)
async def extract_properties(payload: ExtractRequest) -> ExtractResponse:
    return await extract_issue_properties(payload.issue_ids)


@router.get("/v1/metrics/summary", response_model=MetricsSummaryResponse)
async def metrics_summary(
    project_ids: list[int] | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
) -> MetricsSummaryResponse:
    return await get_metrics_summary(
        project_ids=project_ids or [],
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/v1/evals/latest", response_model=EvalArtifactsResponse)
async def evals_latest() -> EvalArtifactsResponse:
    return await get_eval_artifacts_summary()


@router.get("/v1/ops/environment", response_model=OpsEnvironmentResponse)
async def ops_environment() -> OpsEnvironmentResponse:
    return await get_ops_environment()


@router.get("/v1/ops/runs", response_model=OpsRunListResponse)
async def ops_runs(limit: int = Query(default=20, ge=1, le=100)) -> OpsRunListResponse:
    return await list_ops_runs(limit=limit)


@router.post("/v1/ops/backup", response_model=OpsActionResponse)
async def ops_backup(payload: OpsBackupRequest | None = None) -> OpsActionResponse:
    return await run_backup_operation(output_dir=payload.output_dir if payload else None)


@router.post("/v1/ops/maintenance", response_model=OpsActionResponse)
async def ops_maintenance() -> OpsActionResponse:
    return await run_maintenance_operation()
