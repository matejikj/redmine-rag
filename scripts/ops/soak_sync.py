from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, datetime

import httpx

from redmine_rag.core.config import get_settings
from redmine_rag.db.base import Base
from redmine_rag.db.session import get_engine
from redmine_rag.ingestion.redmine_client import RedmineClient
from redmine_rag.ingestion.sync_pipeline import run_incremental_sync
from redmine_rag.mock_redmine.app import app as mock_redmine_app


async def _run_soak(iterations: int, project_ids: list[int]) -> None:
    os.environ["MOCK_REDMINE_DATASET_PROFILE"] = "medium"
    get_settings.cache_clear()
    get_engine.cache_clear()

    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    transport = httpx.ASGITransport(app=mock_redmine_app)
    client = RedmineClient(
        base_url="http://testserver",
        api_key="mock-api-key",
        verify_ssl=False,
        transport=transport,
        extra_headers={"X-Mock-Role": "admin"},
    )

    started = datetime.now(UTC)
    for index in range(iterations):
        summary = await run_incremental_sync(project_ids=project_ids, client=client)
        print(
            f"[{index + 1}/{iterations}] issues={summary['issues_synced']} "
            f"chunks={summary['chunks_updated']} vectors={summary['vectors_upserted']}"
        )
    finished = datetime.now(UTC)
    print(
        f"soak complete: iterations={iterations}, started={started.isoformat()}, "
        f"finished={finished.isoformat()}"
    )
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sync soak test on medium mock dataset")
    parser.add_argument("--iterations", type=int, default=3, help="Number of sync cycles")
    parser.add_argument(
        "--project-id",
        type=int,
        action="append",
        default=[],
        help="Project IDs for sync scope (repeat option to provide multiple ids)",
    )
    args = parser.parse_args()

    project_ids = [project_id for project_id in args.project_id if project_id > 0] or [1]
    asyncio.run(_run_soak(iterations=max(args.iterations, 1), project_ids=project_ids))


if __name__ == "__main__":
    main()
