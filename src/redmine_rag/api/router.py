from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks

from redmine_rag import __version__
from redmine_rag.api.schemas import (
    AskRequest,
    AskResponse,
    ExtractRequest,
    ExtractResponse,
    HealthResponse,
    SyncRequest,
    SyncResponse,
)
from redmine_rag.core.config import get_settings
from redmine_rag.extraction.properties import extract_issue_properties
from redmine_rag.services.ask_service import answer_question
from redmine_rag.services.sync_service import queue_sync_job

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=__version__,
        utc_time=datetime.now(timezone.utc),
    )


@router.post("/v1/ask", response_model=AskResponse)
async def ask(payload: AskRequest) -> AskResponse:
    return await answer_question(payload)


@router.post("/v1/sync/redmine", response_model=SyncResponse)
async def sync_redmine(payload: SyncRequest, background_tasks: BackgroundTasks) -> SyncResponse:
    return await queue_sync_job(payload, background_tasks)


@router.post("/v1/extract/properties", response_model=ExtractResponse)
async def extract_properties(payload: ExtractRequest) -> ExtractResponse:
    return await extract_issue_properties(payload.issue_ids)
