from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    utc_time: datetime


class AskFilters(BaseModel):
    project_ids: list[int] = Field(default_factory=list)
    tracker_ids: list[int] = Field(default_factory=list)
    status_ids: list[int] = Field(default_factory=list)
    from_date: datetime | None = None
    to_date: datetime | None = None


class AskRequest(BaseModel):
    query: str = Field(min_length=3)
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
    project_ids: list[int] | None = None


class SyncResponse(BaseModel):
    job_id: str
    accepted: bool
    detail: str


class ExtractRequest(BaseModel):
    issue_ids: list[int] | None = None


class ExtractResponse(BaseModel):
    accepted: bool
    processed_issues: int
    detail: str
