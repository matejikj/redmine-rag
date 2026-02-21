from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from redmine_rag.core.config import get_settings


class RedmineClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.redmine_base_url.rstrip("/")
        self._api_key = settings.redmine_api_key
        self._verify_ssl = settings.redmine_verify_ssl

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_issues(
        self,
        updated_since: datetime | None,
        project_ids: list[int],
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
            "include": "journals",
        }
        if updated_since is not None:
            params["updated_on"] = f">={updated_since.isoformat()}"
        if project_ids:
            params["project_id"] = ",".join(str(project_id) for project_id in project_ids)

        return await self._get_json("/issues.json", params=params)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_wiki_page(self, project_identifier: str, title: str) -> dict[str, Any]:
        return await self._get_json(f"/projects/{project_identifier}/wiki/{title}.json")

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {"X-Redmine-API-Key": self._api_key}

        async with httpx.AsyncClient(timeout=30, verify=self._verify_ssl) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return payload
