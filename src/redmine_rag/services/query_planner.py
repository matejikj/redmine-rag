from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import orjson
from pydantic import BaseModel, Field, ValidationError, field_validator

from redmine_rag.api.schemas import AskFilters
from redmine_rag.core.config import Settings, get_settings
from redmine_rag.services.llm_runtime import build_llm_runtime_client, resolve_runtime_model

_MAX_QUERY_CHARS = 600


@dataclass(slots=True)
class RetrievalPlanDiagnostics:
    planner_mode: str
    planner_status: str
    latency_ms: int
    normalized_query: str | None
    expansions: list[str]
    confidence: float | None
    error: str | None = None


@dataclass(slots=True)
class RetrievalPlan:
    normalized_query: str
    expansions: list[str]
    suggested_filters: AskFilters
    confidence: float


class PlannerFilterPayload(BaseModel):
    project_ids: list[int] = Field(default_factory=list, max_length=50)
    tracker_ids: list[int] = Field(default_factory=list, max_length=50)
    status_ids: list[int] = Field(default_factory=list, max_length=50)
    from_date: datetime | None = None
    to_date: datetime | None = None

    @field_validator("project_ids", "tracker_ids", "status_ids", mode="before")
    @classmethod
    def normalize_ids(cls, value: object) -> list[int]:
        if not isinstance(value, list):
            return []
        output: list[int] = []
        seen: set[int] = set()
        for item in value:
            try:
                parsed = int(item)
            except (TypeError, ValueError):
                continue
            if parsed <= 0 or parsed in seen:
                continue
            seen.add(parsed)
            output.append(parsed)
        return output


class PlannerPayload(BaseModel):
    normalized_query: str | None = Field(default=None, max_length=_MAX_QUERY_CHARS)
    expansions: list[str] = Field(default_factory=list, max_length=8)
    filters: PlannerFilterPayload = Field(default_factory=PlannerFilterPayload)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("normalized_query")
    @classmethod
    def normalize_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("expansions", mode="before")
    @classmethod
    def normalize_expansions(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        output: list[str] = []
        seen: set[str] = set()
        for item in value:
            normalized = str(item).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(normalized)
        return output


async def build_retrieval_plan(
    *,
    query: str,
    base_filters: AskFilters,
    settings: Settings | None = None,
) -> tuple[RetrievalPlan | None, RetrievalPlanDiagnostics]:
    runtime_settings = settings or get_settings()
    if not runtime_settings.retrieval_planner_enabled:
        return None, RetrievalPlanDiagnostics(
            planner_mode="disabled",
            planner_status="disabled",
            latency_ms=0,
            normalized_query=None,
            expansions=[],
            confidence=None,
        )

    provider = runtime_settings.llm_provider.strip().lower()
    if provider in {"mock", "heuristic", "test"}:
        started = perf_counter()
        plan = _heuristic_plan(
            query=query,
            base_filters=base_filters,
            max_expansions=runtime_settings.retrieval_planner_max_expansions,
        )
        latency_ms = int((perf_counter() - started) * 1000)
        diagnostics = RetrievalPlanDiagnostics(
            planner_mode="heuristic",
            planner_status="applied",
            latency_ms=latency_ms,
            normalized_query=plan.normalized_query,
            expansions=plan.expansions,
            confidence=plan.confidence,
        )
        return plan, diagnostics

    started = perf_counter()
    runtime_client = build_llm_runtime_client(provider=provider, settings=runtime_settings)
    model = resolve_runtime_model(runtime_settings)
    system_prompt = _load_retrieval_planner_system_prompt()
    schema = _load_retrieval_planner_schema()
    user_prompt = _build_user_prompt(query=query, base_filters=base_filters)

    try:
        raw = await runtime_client.generate(
            model=model,
            prompt=user_prompt,
            system_prompt=system_prompt,
            timeout_s=runtime_settings.retrieval_planner_timeout_s,
            response_schema=schema,
        )
        payload = _parse_planner_payload(raw)
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((perf_counter() - started) * 1000)
        return None, RetrievalPlanDiagnostics(
            planner_mode="llm",
            planner_status="failed",
            latency_ms=latency_ms,
            normalized_query=None,
            expansions=[],
            confidence=None,
            error=str(exc),
        )

    if payload is None:
        latency_ms = int((perf_counter() - started) * 1000)
        return None, RetrievalPlanDiagnostics(
            planner_mode="llm",
            planner_status="failed",
            latency_ms=latency_ms,
            normalized_query=None,
            expansions=[],
            confidence=None,
            error="Planner payload is invalid",
        )

    normalized_query = payload.normalized_query or query.strip()
    expansions = _bounded_expansions(
        expansions=payload.expansions,
        normalized_query=normalized_query,
        max_expansions=runtime_settings.retrieval_planner_max_expansions,
    )
    plan = RetrievalPlan(
        normalized_query=normalized_query,
        expansions=expansions,
        suggested_filters=AskFilters(
            project_ids=payload.filters.project_ids,
            tracker_ids=payload.filters.tracker_ids,
            status_ids=payload.filters.status_ids,
            from_date=payload.filters.from_date,
            to_date=payload.filters.to_date,
        ),
        confidence=payload.confidence,
    )
    latency_ms = int((perf_counter() - started) * 1000)
    diagnostics = RetrievalPlanDiagnostics(
        planner_mode="llm",
        planner_status="applied",
        latency_ms=latency_ms,
        normalized_query=plan.normalized_query,
        expansions=plan.expansions,
        confidence=plan.confidence,
    )
    return plan, diagnostics


def _heuristic_plan(*, query: str, base_filters: AskFilters, max_expansions: int) -> RetrievalPlan:
    normalized_query = " ".join(query.split()).strip()
    lowered = normalized_query.lower()
    expansions: list[str] = []

    synonym_groups = [
        ("incident", "outage", "sev"),
        ("oauth", "sso", "single sign on"),
        ("rollback", "revert", "hotfix"),
        ("timeout", "latency", "slow"),
        ("runbook", "playbook", "triage"),
    ]
    for group in synonym_groups:
        hits = [term for term in group if term in lowered]
        if not hits:
            continue
        expansion = " ".join(dict.fromkeys(group))
        if expansion.lower() != normalized_query.lower():
            expansions.append(expansion)
        if len(expansions) >= max(max_expansions, 0):
            break

    project_ids = list(base_filters.project_ids)
    tracker_ids = list(base_filters.tracker_ids)
    status_ids = list(base_filters.status_ids)
    if not project_ids:
        project_ids = _extract_numeric_hints(
            text=normalized_query,
            pattern=r"(?:project|projekt)\s*#?(\d+)",
        )
    if not tracker_ids:
        tracker_ids = _extract_numeric_hints(
            text=normalized_query,
            pattern=r"(?:tracker)\s*#?(\d+)",
        )
    if not status_ids:
        status_ids = _extract_numeric_hints(
            text=normalized_query,
            pattern=r"(?:status)\s*#?(\d+)",
        )

    from_date = base_filters.from_date
    to_date = base_filters.to_date
    if from_date is None or to_date is None:
        hinted_from, hinted_to = _extract_date_hints(normalized_query)
        if from_date is None:
            from_date = hinted_from
        if to_date is None:
            to_date = hinted_to

    return RetrievalPlan(
        normalized_query=normalized_query,
        expansions=_bounded_expansions(
            expansions=expansions,
            normalized_query=normalized_query,
            max_expansions=max_expansions,
        ),
        suggested_filters=AskFilters(
            project_ids=project_ids,
            tracker_ids=tracker_ids,
            status_ids=status_ids,
            from_date=from_date,
            to_date=to_date,
        ),
        confidence=0.55,
    )


def _extract_numeric_hints(*, text: str, pattern: str) -> list[int]:
    output: list[int] = []
    seen: set[int] = set()
    for raw in re.findall(pattern, text, flags=re.IGNORECASE):
        try:
            parsed = int(raw)
        except ValueError:
            continue
        if parsed <= 0 or parsed in seen:
            continue
        seen.add(parsed)
        output.append(parsed)
    return output


def _extract_date_hints(text: str) -> tuple[datetime | None, datetime | None]:
    match = re.search(r"(\d{4}-\d{2}-\d{2})\s*(?:to|do|until|through)\s*(\d{4}-\d{2}-\d{2})", text)
    if not match:
        return None, None
    from_raw, to_raw = match.groups()
    try:
        from_date = datetime.fromisoformat(f"{from_raw}T00:00:00+00:00")
        to_date = datetime.fromisoformat(f"{to_raw}T23:59:59+00:00")
    except ValueError:
        return None, None
    return from_date, to_date


def _bounded_expansions(
    *,
    expansions: list[str],
    normalized_query: str,
    max_expansions: int,
) -> list[str]:
    output: list[str] = []
    seen: set[str] = {normalized_query.strip().lower()}
    for expansion in expansions:
        normalized = expansion.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(normalized)
        if len(output) >= max(max_expansions, 0):
            break
    return output


def _parse_planner_payload(raw_response: str) -> PlannerPayload | None:
    payload = raw_response.strip()
    if not payload:
        return None
    if payload.startswith("```"):
        payload = payload.strip("`").strip()
        if payload.lower().startswith("json"):
            payload = payload[4:].strip()
    try:
        parsed = orjson.loads(payload)
    except orjson.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start < 0 or end < 0 or end <= start:
            return None
        try:
            parsed = orjson.loads(payload[start : end + 1])
        except orjson.JSONDecodeError:
            return None
    if not isinstance(parsed, dict):
        return None
    try:
        return PlannerPayload.model_validate(parsed)
    except ValidationError:
        return None


def _build_user_prompt(*, query: str, base_filters: AskFilters) -> str:
    return (
        "User query:\n"
        f"{query.strip()}\n\n"
        "Current filters:\n"
        f"project_ids={base_filters.project_ids}; "
        f"tracker_ids={base_filters.tracker_ids}; "
        f"status_ids={base_filters.status_ids}; "
        f"from_date={base_filters.from_date}; to_date={base_filters.to_date}\n\n"
        "Return retrieval planning JSON only."
    )


def _load_retrieval_planner_system_prompt() -> str:
    path = _repo_root() / "prompts" / "retrieval_planner_system.md"
    return path.read_text(encoding="utf-8")


def _load_retrieval_planner_schema() -> dict[str, Any]:
    path = _repo_root() / "prompts" / "retrieval_planner_schema.json"
    payload = orjson.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError("Retrieval planner schema must be a JSON object")
    return dict(payload)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
