from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import selectinload

from redmine_rag.api.schemas import ExtractResponse
from redmine_rag.core.config import get_settings
from redmine_rag.db.models import Issue, IssueMetric, IssueProperty, IssueStatus, Journal
from redmine_rag.db.session import get_session_factory
from redmine_rag.extraction.llm_structured import (
    LLM_EXTRACTOR_VERSION,
    PROMPT_VERSION,
    SCHEMA_VERSION,
    LlmExtractionResult,
    StructuredExtractionClient,
    build_structured_extraction_client,
    load_structured_prompt,
    load_structured_schema,
    run_structured_extraction,
)
from redmine_rag.services.guardrail_service import detect_text_violation, record_guardrail_rejection
from redmine_rag.services.llm_runtime import resolve_runtime_model

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "det-v1"


@dataclass(slots=True)
class _StatusMeta:
    name: str
    is_closed: bool


@dataclass(slots=True)
class _StatusTransition:
    old_status_id: int | None
    new_status_id: int | None
    occurred_at: datetime
    journal_id: int


@dataclass(slots=True)
class _AssignmentTransition:
    old_assignee_id: int | None
    new_assignee_id: int | None


@dataclass(slots=True)
class _IssueExtraction:
    issue_id: int
    first_response_s: int | None
    resolution_s: int | None
    reopen_count: int
    touch_count: int
    handoff_count: int
    props_json: dict[str, Any]
    anomaly_count: int
    confidence: float
    extractor_version: str


async def extract_issue_properties(issue_ids: list[int] | None) -> ExtractResponse:
    if issue_ids is not None and not issue_ids:
        return ExtractResponse(
            accepted=True,
            processed_issues=0,
            detail="No issue IDs provided; nothing to extract.",
        )

    settings = get_settings()
    session_factory = get_session_factory()
    extracted_at = datetime.now(UTC)
    llm_enabled = settings.llm_extract_enabled
    llm_model = resolve_runtime_model(settings)
    llm_client: StructuredExtractionClient | None = None
    llm_prompt = ""
    llm_schema: dict[str, Any] = {}
    if llm_enabled:
        llm_client = build_structured_extraction_client(settings.llm_provider)
        llm_prompt = load_structured_prompt()
        llm_schema = load_structured_schema()

    async with session_factory() as session:
        issue_stmt = select(Issue).options(selectinload(Issue.journals)).order_by(Issue.id.asc())
        if issue_ids is not None:
            issue_stmt = issue_stmt.where(Issue.id.in_(issue_ids))

        issues = list((await session.scalars(issue_stmt)).all())
        if not issues:
            return ExtractResponse(
                accepted=True,
                processed_issues=0,
                detail="No issues matched extraction scope.",
            )

        status_rows = (
            await session.execute(select(IssueStatus.id, IssueStatus.name, IssueStatus.is_closed))
        ).all()
        status_meta: dict[int, _StatusMeta] = {
            int(status_id): _StatusMeta(name=str(name), is_closed=bool(is_closed))
            for status_id, name, is_closed in status_rows
        }

        llm_success_count = 0
        llm_failure_count = 0
        llm_skipped_count = 0
        llm_retry_count = 0
        llm_error_buckets: dict[str, int] = {}
        llm_estimated_cost_usd_total = 0.0

        extractions: list[_IssueExtraction] = []
        for batch in _iter_batches(issues, settings.llm_extract_batch_size):
            for issue in batch:
                extraction = _extract_issue(issue, status_meta=status_meta)
                if llm_enabled and llm_client is not None:
                    issue_context = _build_issue_context(
                        issue=issue,
                        max_chars=settings.llm_extract_max_context_chars,
                    )
                    context_violation = detect_text_violation(issue_context)
                    if context_violation is not None:
                        llm_failure_count += 1
                        extraction.confidence = 0.0
                        extraction.extractor_version = _combined_extractor_version()
                        extraction.props_json["llm"] = {
                            "status": "failed",
                            "extractor_version": LLM_EXTRACTOR_VERSION,
                            "prompt_version": PROMPT_VERSION,
                            "schema_version": SCHEMA_VERSION,
                            "attempts": 0,
                            "error_bucket": context_violation,
                            "latency_ms": 0,
                            "estimated_cost_usd": 0.0,
                            "last_error": "Issue context rejected by guardrail before LLM call",
                            "properties": None,
                        }
                        llm_error_buckets[context_violation] = (
                            llm_error_buckets.get(context_violation, 0) + 1
                        )
                        record_guardrail_rejection(
                            context_violation,
                            context="extract.issue_context",
                            detail=issue_context[:180],
                        )
                        extractions.append(extraction)
                        continue

                    estimated_cost_usd = _estimate_extraction_cost_usd(issue_context)
                    if (
                        settings.llm_extract_cost_limit_usd > 0
                        and llm_estimated_cost_usd_total + estimated_cost_usd
                        > settings.llm_extract_cost_limit_usd
                    ):
                        llm_skipped_count += 1
                        extraction.confidence = 0.0
                        extraction.extractor_version = _combined_extractor_version()
                        extraction.props_json["llm"] = {
                            "status": "skipped",
                            "extractor_version": LLM_EXTRACTOR_VERSION,
                            "prompt_version": PROMPT_VERSION,
                            "schema_version": SCHEMA_VERSION,
                            "attempts": 0,
                            "error_bucket": "cost_limit_reached",
                            "latency_ms": 0,
                            "estimated_cost_usd": estimated_cost_usd,
                            "last_error": None,
                            "properties": None,
                        }
                        extractions.append(extraction)
                        continue

                    llm_result = await run_structured_extraction(
                        client=llm_client,
                        system_prompt=llm_prompt,
                        user_content=issue_context,
                        schema=llm_schema,
                        model=llm_model,
                        timeout_s=settings.llm_extract_timeout_s,
                        max_retries=settings.llm_extract_max_retries,
                    )
                    llm_estimated_cost_usd_total += estimated_cost_usd
                    llm_retry_count += max(llm_result.attempts - 1, 0)
                    if llm_result.success:
                        llm_success_count += 1
                        extraction.confidence = (
                            llm_result.properties.confidence
                            if llm_result.properties is not None
                            else 0.0
                        )
                        extraction.extractor_version = _combined_extractor_version()
                        extraction.props_json["llm"] = _llm_payload_from_result(
                            llm_result=llm_result,
                            estimated_cost_usd=estimated_cost_usd,
                        )
                    else:
                        llm_failure_count += 1
                        extraction.confidence = 0.0
                        extraction.extractor_version = _combined_extractor_version()
                        extraction.props_json["llm"] = _llm_payload_from_result(
                            llm_result=llm_result,
                            estimated_cost_usd=estimated_cost_usd,
                        )
                        if llm_result.error_bucket is not None:
                            llm_error_buckets[llm_result.error_bucket] = (
                                llm_error_buckets.get(llm_result.error_bucket, 0) + 1
                            )
                else:
                    llm_skipped_count += 1
                    extraction.props_json["llm"] = {
                        "status": "skipped",
                        "extractor_version": LLM_EXTRACTOR_VERSION,
                        "prompt_version": PROMPT_VERSION,
                        "schema_version": SCHEMA_VERSION,
                        "attempts": 0,
                        "error_bucket": "llm_extract_disabled",
                        "latency_ms": 0,
                        "estimated_cost_usd": 0.0,
                        "last_error": None,
                        "properties": None,
                    }
                extractions.append(extraction)
        metric_rows = [
            {
                "issue_id": extraction.issue_id,
                "first_response_s": extraction.first_response_s,
                "resolution_s": extraction.resolution_s,
                "reopen_count": extraction.reopen_count,
                "touch_count": extraction.touch_count,
                "handoff_count": extraction.handoff_count,
            }
            for extraction in extractions
        ]
        property_rows = [
            {
                "issue_id": extraction.issue_id,
                "extractor_version": extraction.extractor_version,
                "confidence": extraction.confidence,
                "props_json": extraction.props_json,
                "extracted_at": extracted_at,
            }
            for extraction in extractions
        ]

        await _upsert_issue_metrics(session=session, rows=metric_rows)
        await _upsert_issue_properties(session=session, rows=property_rows)
        await session.commit()

    total_anomalies = sum(extraction.anomaly_count for extraction in extractions)
    logger.info(
        "Issue extraction finished",
        extra={
            "processed_issues": len(extractions),
            "extractor_version": EXTRACTOR_VERSION,
            "anomaly_count": total_anomalies,
            "scope_issue_ids": issue_ids,
            "llm_enabled": llm_enabled,
            "llm_success_count": llm_success_count,
            "llm_failure_count": llm_failure_count,
            "llm_skipped_count": llm_skipped_count,
            "llm_retry_count": llm_retry_count,
            "llm_error_buckets": llm_error_buckets,
            "llm_estimated_cost_usd_total": round(llm_estimated_cost_usd_total, 6),
        },
    )
    llm_summary = ""
    if llm_enabled:
        llm_summary = (
            f" LLM ok={llm_success_count}, failed={llm_failure_count}, "
            f"skipped={llm_skipped_count}, retries={llm_retry_count}."
        )
    return ExtractResponse(
        accepted=True,
        processed_issues=len(extractions),
        detail=(
            f"Deterministic extraction completed with {total_anomalies} anomaly markers "
            f"(extractor={EXTRACTOR_VERSION}).{llm_summary}"
        ),
    )


def _extract_issue(issue: Issue, *, status_meta: dict[int, _StatusMeta]) -> _IssueExtraction:
    created_on = _ensure_utc(issue.created_on)
    journals = sorted(
        issue.journals,
        key=lambda journal: (_ensure_utc(journal.created_on), int(journal.id)),
    )

    status_transitions: list[_StatusTransition] = []
    assignment_transitions: list[_AssignmentTransition] = []
    anomalies: set[str] = set()
    unknown_status_ids: set[int] = set()
    invalid_transition_count = 0
    timestamp_anomaly_count = 0
    touch_count = len(journals)
    first_response_at: datetime | None = None
    previous_journal_at: datetime | None = None

    for journal in journals:
        journal_at = _ensure_utc(journal.created_on)
        if journal_at < created_on:
            timestamp_anomaly_count += 1
            anomalies.add("journal_before_issue_created")
        if previous_journal_at is not None and journal_at < previous_journal_at:
            timestamp_anomaly_count += 1
            anomalies.add("journal_timestamp_out_of_order")
        previous_journal_at = journal_at

        if first_response_at is None and journal_at >= created_on:
            first_response_at = journal_at

        for detail in _extract_detail_items(journal):
            name = str(detail.get("name", "")).strip()
            if name == "status_id":
                old_status_id = _to_int_or_none(detail.get("old_value"))
                new_status_id = _to_int_or_none(detail.get("new_value"))
                if old_status_id is None or new_status_id is None:
                    invalid_transition_count += 1
                    anomalies.add("status_transition_missing_value")
                status_transitions.append(
                    _StatusTransition(
                        old_status_id=old_status_id,
                        new_status_id=new_status_id,
                        occurred_at=journal_at,
                        journal_id=int(journal.id),
                    )
                )
                continue

            if name == "assigned_to_id":
                assignment_transitions.append(
                    _AssignmentTransition(
                        old_assignee_id=_to_int_or_none(detail.get("old_value")),
                        new_assignee_id=_to_int_or_none(detail.get("new_value")),
                    )
                )

    status_path: list[int] = []
    last_status_id: int | None = None
    resolution_at: datetime | None = None
    reopen_count = 0

    for transition in status_transitions:
        old_status_id = transition.old_status_id
        new_status_id = transition.new_status_id

        if old_status_id is not None and old_status_id not in status_meta:
            unknown_status_ids.add(old_status_id)
            anomalies.add("unknown_status_id")
        if new_status_id is not None and new_status_id not in status_meta:
            unknown_status_ids.add(new_status_id)
            anomalies.add("unknown_status_id")

        if last_status_id is None and old_status_id is not None:
            status_path.append(old_status_id)
            last_status_id = old_status_id
        elif (
            old_status_id is not None
            and last_status_id is not None
            and old_status_id != last_status_id
        ):
            invalid_transition_count += 1
            anomalies.add("status_transition_chain_break")
            status_path.append(old_status_id)
            last_status_id = old_status_id

        if new_status_id is not None:
            status_path.append(new_status_id)
            if _is_reopen_transition(
                status_meta=status_meta,
                old_status_id=old_status_id,
                new_status_id=new_status_id,
            ):
                reopen_count += 1
            if resolution_at is None and _status_is_closed(status_meta, new_status_id):
                resolution_at = transition.occurred_at
            last_status_id = new_status_id

    if not status_path and issue.status_id is not None:
        status_path.append(int(issue.status_id))

    if resolution_at is None and issue.closed_on is not None:
        closed_on = _ensure_utc(issue.closed_on)
        if closed_on >= created_on:
            resolution_at = closed_on
        else:
            anomalies.add("closed_on_before_issue_created")

    if (
        resolution_at is not None
        and first_response_at is not None
        and resolution_at < first_response_at
    ):
        anomalies.add("resolution_before_first_response")

    if (
        issue.closed_on is not None
        and resolution_at is not None
        and _ensure_utc(issue.closed_on) < resolution_at
    ):
        anomalies.add("closed_on_before_resolution_transition")

    first_response_s = _seconds_since(start=created_on, end=first_response_at)
    if first_response_at is not None and first_response_s is None:
        anomalies.add("invalid_first_response_duration")

    resolution_s = _seconds_since(start=created_on, end=resolution_at)
    if resolution_at is not None and resolution_s is None:
        anomalies.add("invalid_resolution_duration")

    handoff_count = sum(
        1
        for transition in assignment_transitions
        if transition.old_assignee_id is not None
        and transition.new_assignee_id is not None
        and transition.old_assignee_id != transition.new_assignee_id
    )

    props_json = {
        "status_path": status_path,
        "current_status_id": issue.status_id,
        "current_status": issue.status,
        "first_response_at": _to_iso(first_response_at),
        "resolved_at": _to_iso(resolution_at),
        "validation": {
            "anomalies": sorted(anomalies),
            "timestamp_anomaly_count": timestamp_anomaly_count,
            "invalid_status_transition_count": invalid_transition_count,
            "unknown_status_ids": sorted(unknown_status_ids),
        },
        "event_counts": {
            "journals": touch_count,
            "status_transitions": len(status_transitions),
            "assignment_transitions": len(assignment_transitions),
        },
    }

    return _IssueExtraction(
        issue_id=int(issue.id),
        first_response_s=first_response_s,
        resolution_s=resolution_s,
        reopen_count=reopen_count,
        touch_count=touch_count,
        handoff_count=handoff_count,
        props_json=props_json,
        anomaly_count=(
            timestamp_anomaly_count + invalid_transition_count + len(unknown_status_ids)
        ),
        confidence=1.0,
        extractor_version=EXTRACTOR_VERSION,
    )


async def _upsert_issue_metrics(*, session: Any, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    stmt = sqlite_insert(IssueMetric).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["issue_id"],
        set_={
            "first_response_s": stmt.excluded.first_response_s,
            "resolution_s": stmt.excluded.resolution_s,
            "reopen_count": stmt.excluded.reopen_count,
            "touch_count": stmt.excluded.touch_count,
            "handoff_count": stmt.excluded.handoff_count,
        },
    )
    await session.execute(stmt)


async def _upsert_issue_properties(*, session: Any, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    stmt = sqlite_insert(IssueProperty).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["issue_id"],
        set_={
            "extractor_version": stmt.excluded.extractor_version,
            "confidence": stmt.excluded.confidence,
            "props_json": stmt.excluded.props_json,
            "extracted_at": stmt.excluded.extracted_at,
        },
    )
    await session.execute(stmt)


def _extract_detail_items(journal: Journal) -> list[dict[str, Any]]:
    details = journal.details
    if isinstance(details, dict):
        items = details.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    if isinstance(details, list):
        return [item for item in details if isinstance(item, dict)]
    return []


def _is_reopen_transition(
    *,
    status_meta: dict[int, _StatusMeta],
    old_status_id: int | None,
    new_status_id: int,
) -> bool:
    new_name = status_meta.get(new_status_id, _StatusMeta(name="", is_closed=False)).name.lower()
    if "reopen" in new_name:
        return True
    if old_status_id is None:
        return False
    return _status_is_closed(status_meta, old_status_id) and not _status_is_closed(
        status_meta, new_status_id
    )


def _status_is_closed(status_meta: dict[int, _StatusMeta], status_id: int) -> bool:
    metadata = status_meta.get(status_id)
    if metadata is None:
        return False
    return metadata.is_closed


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _seconds_since(*, start: datetime, end: datetime | None) -> int | None:
    if end is None:
        return None
    delta = int((end - start).total_seconds())
    if delta < 0:
        return None
    return delta


def _to_int_or_none(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError:
            return None
    return None


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _combined_extractor_version() -> str:
    return f"{EXTRACTOR_VERSION}+{LLM_EXTRACTOR_VERSION}"


def _llm_payload_from_result(
    *,
    llm_result: LlmExtractionResult,
    estimated_cost_usd: float,
) -> dict[str, Any]:
    status = "ok" if llm_result.success else "failed"
    properties_payload: dict[str, Any] | None = None
    if llm_result.properties is not None:
        properties_payload = llm_result.properties.model_dump(mode="json")
    return {
        "status": status,
        "extractor_version": LLM_EXTRACTOR_VERSION,
        "prompt_version": PROMPT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "attempts": llm_result.attempts,
        "error_bucket": llm_result.error_bucket,
        "latency_ms": llm_result.latency_ms,
        "estimated_cost_usd": estimated_cost_usd,
        "last_error": llm_result.last_error,
        "properties": properties_payload,
    }


def _iter_batches(items: list[Issue], batch_size: int) -> list[list[Issue]]:
    safe_batch_size = max(batch_size, 1)
    return [
        items[index : index + safe_batch_size] for index in range(0, len(items), safe_batch_size)
    ]


def _build_issue_context(*, issue: Issue, max_chars: int) -> str:
    lines = [
        f"Issue id: {issue.id}",
        f"Project id: {issue.project_id}",
        f"Tracker: {issue.tracker or ''}",
        f"Status: {issue.status or ''}",
        f"Priority: {issue.priority or ''}",
        f"Subject: {issue.subject}",
        f"Description: {issue.description or ''}",
    ]
    if issue.custom_fields:
        lines.append(f"Custom fields: {issue.custom_fields}")

    journals = sorted(
        issue.journals,
        key=lambda journal: (_ensure_utc(journal.created_on), int(journal.id)),
    )
    for journal in journals:
        details = _extract_detail_items(journal)
        detail_lines = []
        for detail in details:
            name = str(detail.get("name", "")).strip()
            old_value = str(detail.get("old_value", "")).strip()
            new_value = str(detail.get("new_value", "")).strip()
            if name:
                detail_lines.append(f"{name}:{old_value}->{new_value}")
        lines.append(
            "Journal "
            f"{journal.id} at {journal.created_on.isoformat()} "
            f"by {journal.author or journal.user_id}: {journal.notes or ''}"
        )
        if detail_lines:
            lines.append(f"Journal {journal.id} details: {', '.join(detail_lines)}")

    context = "\n".join(lines).strip()
    if len(context) <= max_chars:
        return context
    return context[:max_chars]


def _estimate_extraction_cost_usd(context: str) -> float:
    # Local deterministic estimate: approximately 750 chars ~ 1k tokens.
    estimated_tokens = max(len(context) / 0.75, 1.0)
    return round((estimated_tokens / 1000.0) * 0.0006, 6)
