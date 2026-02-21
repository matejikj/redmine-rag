from __future__ import annotations

from redmine_rag.api.schemas import ExtractResponse


async def extract_issue_properties(issue_ids: list[int] | None) -> ExtractResponse:
    """Placeholder for deterministic + LLM property extraction pipeline."""

    processed = len(issue_ids) if issue_ids is not None else 0
    return ExtractResponse(
        accepted=True,
        processed_issues=processed,
        detail="Extraction pipeline scaffold is ready; implement domain extractors next.",
    )
