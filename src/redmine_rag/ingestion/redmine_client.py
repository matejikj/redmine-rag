from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from redmine_rag.core.config import get_settings


class RedmineClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        verify_ssl: bool | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.redmine_base_url).rstrip("/")
        self._api_key = api_key or settings.redmine_api_key
        self._verify_ssl = settings.redmine_verify_ssl if verify_ssl is None else verify_ssl
        self._transport = transport
        self._extra_headers = extra_headers or {}

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_issues(
        self,
        updated_since: datetime | None,
        project_ids: list[int],
        include_fields: tuple[str, ...] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        includes = include_fields or (
            "journals",
            "attachments",
            "relations",
            "watchers",
            "children",
        )
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
            "include": ",".join(includes),
        }
        if updated_since is not None:
            params["updated_on"] = f">={updated_since.isoformat()}"
        if project_ids:
            params["project_id"] = ",".join(str(project_id) for project_id in project_ids)

        return await self._get_json("/issues.json", params=params)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_projects(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await self._get_json("/projects.json", params={"limit": limit, "offset": offset})

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_users(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await self._get_json("/users.json", params={"limit": limit, "offset": offset})

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_groups(self, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await self._get_json("/groups.json", params={"limit": limit, "offset": offset})

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_trackers(self) -> dict[str, Any]:
        return await self._get_json("/trackers.json")

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_issue_statuses(self) -> dict[str, Any]:
        return await self._get_json("/issue_statuses.json")

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_issue_priorities(self) -> dict[str, Any]:
        return await self._get_json("/enumerations/issue_priorities.json")

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_time_entries(
        self,
        updated_since: datetime | None,
        project_ids: list[int],
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
        }
        if updated_since is not None:
            params["updated_on"] = f">={updated_since.isoformat()}"
        if project_ids:
            params["project_id"] = ",".join(str(project_id) for project_id in project_ids)
        return await self._get_json("/time_entries.json", params=params)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_news(
        self,
        project_ids: list[int],
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
        }
        if project_ids:
            params["project_id"] = ",".join(str(project_id) for project_id in project_ids)
        return await self._get_json("/news.json", params=params)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_documents(
        self,
        project_ids: list[int],
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
        }
        if project_ids:
            params["project_id"] = ",".join(str(project_id) for project_id in project_ids)
        return await self._get_json("/documents.json", params=params)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_files(
        self,
        project_ids: list[int],
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "limit": limit,
            "offset": offset,
        }
        if project_ids:
            params["project_id"] = ",".join(str(project_id) for project_id in project_ids)
        return await self._get_json("/files.json", params=params)

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_board_topics(
        self, board_id: int, limit: int = 100, offset: int = 0
    ) -> dict[str, Any]:
        return await self._get_json(
            f"/boards/{board_id}/topics.json",
            params={"limit": limit, "offset": offset},
        )

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_message(self, message_id: int) -> dict[str, Any]:
        return await self._get_json(f"/messages/{message_id}.json")

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
    async def get_wiki_page(self, project_identifier: str, title: str) -> dict[str, Any]:
        return await self._get_json(f"/projects/{project_identifier}/wiki/{title}.json")

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {"X-Redmine-API-Key": self._api_key, **self._extra_headers}

        async with httpx.AsyncClient(
            timeout=30,
            verify=self._verify_ssl,
            transport=self._transport,
        ) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return payload
