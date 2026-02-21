from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


async def run_periodic_sync_loop(interval_seconds: int = 900) -> None:
    """Simple periodic loop placeholder.

    Replace this with APScheduler/RQ/Celery when workload requires distributed workers.
    """

    while True:
        logger.info("Periodic sync tick", extra={"interval_seconds": interval_seconds})
        await asyncio.sleep(interval_seconds)
