from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

PositiveInt = Annotated[int, Field(gt=0)]
SYNC_MODULE_CHOICES: tuple[str, ...] = (
    "projects",
    "users",
    "groups",
    "trackers",
    "issue_statuses",
    "issue_priorities",
    "issues",
    "time_entries",
    "news",
    "documents",
    "files",
    "boards",
    "wiki",
)


class HealthCheck(BaseModel):
    name: str
    status: Literal["ok", "warn", "fail"]
    detail: str | None = None
    latency_ms: int | None = None


class SyncJobCounts(BaseModel):
    queued: int = 0
    running: int = 0
    finished: int = 0
    failed: int = 0


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    utc_time: datetime
    checks: list[HealthCheck] = Field(default_factory=list)
    sync_jobs: SyncJobCounts = Field(default_factory=SyncJobCounts)


class AskFilters(BaseModel):
    project_ids: list[PositiveInt] = Field(default_factory=list)
    tracker_ids: list[PositiveInt] = Field(default_factory=list)
    status_ids: list[PositiveInt] = Field(default_factory=list)
    from_date: datetime | None = None
    to_date: datetime | None = None


class AskRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1200)
    filters: AskFilters = Field(default_factory=AskFilters)
    top_k: int = Field(default=8, ge=1, le=30)


class Citation(BaseModel):
    id: int
    url: str
    source_type: str
    source_id: str
    snippet: str


class AskResponse(BaseModel):
    answer_markdown: str
    citations: list[Citation]
    used_chunk_ids: list[int]
    confidence: float = Field(ge=0.0, le=1.0)


class SyncRequest(BaseModel):
    project_ids: list[PositiveInt] | None = Field(default=None, max_length=200)
    modules: list[str] | None = Field(default=None, max_length=len(SYNC_MODULE_CHOICES))

    @field_validator("modules", mode="before")
    @classmethod
    def normalize_modules(cls, value: object) -> list[str] | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            candidates = [item.strip().lower() for item in value.split(",") if item.strip()]
        elif isinstance(value, list):
            candidates = [str(item).strip().lower() for item in value if str(item).strip()]
        else:
            raise ValueError("Invalid modules payload")

        normalized: list[str] = []
        seen: set[str] = set()
        allowed = set(SYNC_MODULE_CHOICES)
        for module in candidates:
            if module not in allowed:
                raise ValueError(f"Unsupported module '{module}'")
            if module in seen:
                continue
            seen.add(module)
            normalized.append(module)
        return normalized or None


class SyncResponse(BaseModel):
    job_id: str
    accepted: bool
    detail: str


class ExtractRequest(BaseModel):
    issue_ids: list[PositiveInt] | None = Field(default=None, max_length=1000)


class ExtractResponse(BaseModel):
    accepted: bool
    processed_issues: int
    detail: str


class SyncJobResponse(BaseModel):
    id: str
    status: str
    payload: dict
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class SyncJobListResponse(BaseModel):
    items: list[SyncJobResponse]
    total: int
    counts: SyncJobCounts


class MetricsSummaryByProject(BaseModel):
    project_id: int
    issues_total: int
    issues_with_first_response: int
    issues_with_resolution: int
    avg_first_response_s: float | None
    avg_resolution_s: float | None
    reopen_total: int
    touch_total: int
    handoff_total: int


class MetricsSummaryResponse(BaseModel):
    generated_at: datetime
    from_date: datetime | None
    to_date: datetime | None
    project_ids: list[int]
    extractor_version: str
    issues_total: int
    issues_with_first_response: int
    issues_with_resolution: int
    avg_first_response_s: float | None
    avg_resolution_s: float | None
    reopen_total: int
    touch_total: int
    handoff_total: int
    by_project: list[MetricsSummaryByProject]
