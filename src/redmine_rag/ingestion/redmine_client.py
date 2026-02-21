from __future__ import annotations

import logging
from datetime import datetime
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from redmine_rag.core.config import get_settings

logger = logging.getLogger(__name__)


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
        self._timeout_s = settings.redmine_http_timeout_s
        self._allowed_hosts = {
            host.strip().lower() for host in settings.redmine_allowed_hosts if host.strip()
        }
        self._validate_outbound_base_url()

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
            timeout=self._timeout_s,
            verify=self._verify_ssl,
            transport=self._transport,
        ) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return payload

    def _validate_outbound_base_url(self) -> None:
        parsed = urlparse(self._base_url)
        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise ValueError("Redmine base URL hostname is required")
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Redmine base URL must use http or https")

        localhost_names = {"127.0.0.1", "localhost", "::1", "testserver"}
        is_localhost = hostname in localhost_names
        if parsed.scheme != "https" and not is_localhost:
            raise ValueError(f"Outbound policy blocked non-HTTPS Redmine URL host={hostname!r}")
        if self._allowed_hosts and hostname not in self._allowed_hosts:
            raise ValueError(
                f"Outbound policy blocked Redmine URL host={hostname!r}, "
                "host not in REDMINE_ALLOWED_HOSTS"
            )
        if _is_private_ip(hostname) and not is_localhost:
            logger.warning(
                "Redmine outbound host resolves to private IP; verify allowlist policy",
                extra={"redmine_host": hostname},
            )


def _is_private_ip(hostname: str) -> bool:
    try:
        ip = ip_address(hostname)
    except ValueError:
        return False
    return bool(ip.is_private)
