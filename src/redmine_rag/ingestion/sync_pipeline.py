from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from redmine_rag.core.config import get_settings

logger = logging.getLogger(__name__)


async def run_incremental_sync(project_ids: list[int]) -> dict[str, Any]:
    """Run one sync cycle.

    This is intentionally conservative for initial infrastructure.
    It provides a stable integration point for the full ETL implementation.
    """

    settings = get_settings()
    effective_project_ids = project_ids or settings.redmine_project_ids

    logger.info(
        "Starting incremental Redmine sync",
        extra={
            "project_ids": effective_project_ids,
            "overlap_minutes": settings.sync_overlap_minutes,
        },
    )

    summary: dict[str, Any] = {
        "project_ids": effective_project_ids,
        "issues_synced": 0,
        "journals_synced": 0,
        "wiki_pages_synced": 0,
        "chunks_updated": 0,
        "finished_at": datetime.now(UTC).isoformat(),
    }

    logger.info("Finished incremental Redmine sync", extra=summary)
    return summary
