from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.core.config import get_settings
from redmine_rag.db.models import Project, SyncCursor, SyncState
from redmine_rag.db.session import get_session_factory
from redmine_rag.indexing.chunk_indexer import ChunkIndexer
from redmine_rag.indexing.embedding_indexer import EmbeddingIndexer
from redmine_rag.indexing.vector_store import LocalNumpyVectorStore
from redmine_rag.ingestion.redmine_client import RedmineClient
from redmine_rag.ingestion.repository import IngestionRepository

logger = logging.getLogger(__name__)

MODULE_ORDER = (
    "projects",
    "users",
    "groups",
    "trackers",
    "issue_statuses",
    "issue_priorities",
    "issues",
    "time_entries",
    "news",
    "documents",
    "files",
    "boards",
    "wiki",
)


@dataclass(slots=True)
class SyncContext:
    session: AsyncSession
    repo: IngestionRepository
    client: RedmineClient
    effective_project_ids: list[int]
    fetched_at: datetime
    overlap_minutes: int
    board_ids: list[int]
    wiki_pages: list[str]
    base_url: str


async def run_incremental_sync(
    project_ids: list[int],
    *,
    client: RedmineClient | None = None,
    modules_override: list[str] | None = None,
) -> dict[str, Any]:
    """Run one full incremental sync cycle with deterministic module ordering."""

    settings = get_settings()
    effective_project_ids = project_ids or settings.redmine_project_ids
    enabled_modules = (
        set(modules_override) if modules_override else set(settings.redmine_modules or MODULE_ORDER)
    )
    fetched_at = datetime.now(UTC)

    summary: dict[str, Any] = {
        "project_ids": effective_project_ids,
        "modules_enabled": sorted(enabled_modules),
        "modules_skipped": [],
        "projects_synced": 0,
        "users_synced": 0,
        "groups_synced": 0,
        "trackers_synced": 0,
        "issue_statuses_synced": 0,
        "issue_priorities_synced": 0,
        "issues_synced": 0,
        "journals_synced": 0,
        "custom_fields_synced": 0,
        "relations_synced": 0,
        "watchers_synced": 0,
        "attachments_synced": 0,
        "time_entries_synced": 0,
        "news_synced": 0,
        "documents_synced": 0,
        "files_synced": 0,
        "boards_synced": 0,
        "messages_synced": 0,
        "wiki_pages_synced": 0,
        "wiki_versions_synced": 0,
        "raw_entities_synced": 0,
        "raw_issues_synced": 0,
        "raw_journals_synced": 0,
        "raw_wiki_synced": 0,
        "chunk_sources_reindexed": 0,
        "chunks_updated": 0,
        "embeddings_processed": 0,
        "vectors_upserted": 0,
        "vectors_removed": 0,
        "finished_at": None,
    }

    logger.info(
        "Starting incremental Redmine sync",
        extra={
            "project_ids": effective_project_ids,
            "enabled_modules": sorted(enabled_modules),
            "overlap_minutes": settings.sync_overlap_minutes,
        },
    )

    session_factory = get_session_factory()
    sync_client = client or RedmineClient()
    async with session_factory() as session:
        repo = IngestionRepository(session)
        sync_state = await _get_or_create_sync_state(session, key="redmine_incremental")
        previous_success_at = sync_state.last_success_at
        sync_state.last_sync_at = fetched_at
        sync_state.last_error = None
        await session.commit()

        context = SyncContext(
            session=session,
            repo=repo,
            client=sync_client,
            effective_project_ids=effective_project_ids,
            fetched_at=fetched_at,
            overlap_minutes=settings.sync_overlap_minutes,
            board_ids=settings.redmine_board_ids,
            wiki_pages=settings.redmine_wiki_pages,
            base_url=settings.redmine_base_url.rstrip("/"),
        )

        handlers: dict[str, Callable[[SyncContext, dict[str, Any]], Awaitable[None]]] = {
            "projects": _sync_projects,
            "users": _sync_users,
            "groups": _sync_groups,
            "trackers": _sync_trackers,
            "issue_statuses": _sync_issue_statuses,
            "issue_priorities": _sync_issue_priorities,
            "issues": _sync_issues,
            "time_entries": _sync_time_entries,
            "news": _sync_news,
            "documents": _sync_documents,
            "files": _sync_files,
            "boards": _sync_boards_and_messages,
            "wiki": _sync_wiki,
        }

        try:
            for module_name in MODULE_ORDER:
                if module_name not in enabled_modules:
                    summary["modules_skipped"].append(
                        {"module": module_name, "reason": "disabled_by_configuration"}
                    )
                    continue

                handler = handlers[module_name]
                try:
                    logger.info("Running sync module", extra={"sync_module": module_name})
                    await handler(context, summary)
                    await session.commit()
                    logger.info("Sync module finished", extra={"sync_module": module_name})
                except httpx.HTTPStatusError as exc:
                    status_code = exc.response.status_code
                    if status_code in {403, 404, 405, 501}:
                        await session.rollback()
                        logger.warning(
                            "Skipping unsupported module",
                            extra={
                                "sync_module": module_name,
                                "status_code": status_code,
                                "detail": str(exc),
                            },
                        )
                        summary["modules_skipped"].append(
                            {
                                "module": module_name,
                                "reason": "endpoint_not_available",
                                "status_code": status_code,
                            }
                        )
                        continue
                    raise

            chunk_indexer = ChunkIndexer(
                session,
                base_url=context.base_url,
            )
            chunk_since = _cursor_lower_bound(previous_success_at, context.overlap_minutes)
            chunk_stats = await chunk_indexer.refresh(since=chunk_since)
            summary["chunk_sources_reindexed"] = chunk_stats.sources_reindexed
            summary["chunks_updated"] = chunk_stats.chunks_updated

            vector_store = LocalNumpyVectorStore(
                index_path=settings.vector_index_path,
                meta_path=settings.vector_meta_path,
            )
            embedding_indexer = EmbeddingIndexer(
                session=session,
                store=vector_store,
                embedding_dim=settings.embedding_dim,
            )
            embedding_stats = await embedding_indexer.refresh(since=chunk_since, full_rebuild=False)
            summary["embeddings_processed"] = embedding_stats.processed_chunks
            summary["vectors_upserted"] = embedding_stats.vectors_upserted
            summary["vectors_removed"] = embedding_stats.removed_vectors

            sync_state.last_success_at = datetime.now(UTC)
            sync_state.last_error = None
            summary["finished_at"] = datetime.now(UTC).isoformat()
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            sync_state.last_error = str(exc)
            await session.commit()
            logger.exception(
                "Incremental Redmine sync failed", extra={"project_ids": effective_project_ids}
            )
            raise

    logger.info("Finished incremental Redmine sync", extra=summary)
    return summary


async def _sync_projects(context: SyncContext, summary: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    async for items in _iter_paginated(
        lambda limit, offset: context.client.get_projects(limit=limit, offset=offset),
        payload_key="projects",
    ):
        for project in items:
            project_id = int(project["id"])
            rows.append(
                {
                    "id": project_id,
                    "identifier": str(project["identifier"]),
                    "name": str(project["name"]),
                    "description": _to_str_or_none(project.get("description")),
                    "status": int(project.get("status", 1)),
                    "is_public": bool(project.get("is_public", True)),
                    "parent_id": _to_int_or_none(project.get("parent_id")),
                    "homepage": _to_str_or_none(project.get("homepage")),
                    "created_on": _parse_datetime(project.get("created_on")),
                    "updated_on": _parse_datetime(project.get("updated_on")),
                }
            )
            raw_rows.append(
                {
                    "entity_type": "project",
                    "entity_id": str(project_id),
                    "endpoint": "/projects.json",
                    "project_id": project_id,
                    "updated_on": _parse_datetime(project.get("updated_on")),
                    "fetched_at": context.fetched_at,
                    "payload": project,
                }
            )

    summary["projects_synced"] += await context.repo.upsert_projects(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_users(context: SyncContext, summary: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    async for items in _iter_paginated(
        lambda limit, offset: context.client.get_users(limit=limit, offset=offset),
        payload_key="users",
    ):
        for user in items:
            user_id = int(user["id"])
            rows.append(
                {
                    "id": user_id,
                    "login": str(user["login"]),
                    "firstname": _to_str_or_none(user.get("firstname")),
                    "lastname": _to_str_or_none(user.get("lastname")),
                    "mail": _to_str_or_none(user.get("mail")),
                    "admin": bool(user.get("admin", False)),
                    "status": int(user.get("status", 1)),
                    "last_login_on": _parse_datetime(user.get("last_login_on")),
                    "created_on": _parse_datetime(user.get("created_on")),
                    "updated_on": _parse_datetime(user.get("updated_on")),
                }
            )
            raw_rows.append(
                {
                    "entity_type": "user",
                    "entity_id": str(user_id),
                    "endpoint": "/users.json",
                    "project_id": None,
                    "updated_on": _parse_datetime(user.get("updated_on")),
                    "fetched_at": context.fetched_at,
                    "payload": user,
                }
            )

    summary["users_synced"] += await context.repo.upsert_users(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_groups(context: SyncContext, summary: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    async for items in _iter_paginated(
        lambda limit, offset: context.client.get_groups(limit=limit, offset=offset),
        payload_key="groups",
    ):
        for group in items:
            group_id = int(group["id"])
            rows.append(
                {
                    "id": group_id,
                    "name": str(group["name"]),
                    "users_json": list(group.get("users", [])),
                }
            )
            raw_rows.append(
                {
                    "entity_type": "group",
                    "entity_id": str(group_id),
                    "endpoint": "/groups.json",
                    "project_id": None,
                    "updated_on": None,
                    "fetched_at": context.fetched_at,
                    "payload": group,
                }
            )

    summary["groups_synced"] += await context.repo.upsert_groups(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_trackers(context: SyncContext, summary: dict[str, Any]) -> None:
    payload = await context.client.get_trackers()
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    for tracker in payload.get("trackers", []):
        tracker_id = int(tracker["id"])
        rows.append(
            {
                "id": tracker_id,
                "name": str(tracker["name"]),
                "default_status_id": _to_int_or_none(tracker.get("default_status_id")),
                "description": _to_str_or_none(tracker.get("description")),
            }
        )
        raw_rows.append(
            {
                "entity_type": "tracker",
                "entity_id": str(tracker_id),
                "endpoint": "/trackers.json",
                "project_id": None,
                "updated_on": None,
                "fetched_at": context.fetched_at,
                "payload": tracker,
            }
        )

    summary["trackers_synced"] += await context.repo.upsert_trackers(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_issue_statuses(context: SyncContext, summary: dict[str, Any]) -> None:
    payload = await context.client.get_issue_statuses()
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    for status in payload.get("issue_statuses", []):
        status_id = int(status["id"])
        rows.append(
            {
                "id": status_id,
                "name": str(status["name"]),
                "is_closed": bool(status.get("is_closed", False)),
                "is_default": bool(status.get("is_default", False)),
            }
        )
        raw_rows.append(
            {
                "entity_type": "issue_status",
                "entity_id": str(status_id),
                "endpoint": "/issue_statuses.json",
                "project_id": None,
                "updated_on": None,
                "fetched_at": context.fetched_at,
                "payload": status,
            }
        )

    summary["issue_statuses_synced"] += await context.repo.upsert_issue_statuses(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_issue_priorities(context: SyncContext, summary: dict[str, Any]) -> None:
    payload = await context.client.get_issue_priorities()
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    for priority in payload.get("issue_priorities", []):
        priority_id = int(priority["id"])
        rows.append(
            {
                "id": priority_id,
                "name": str(priority["name"]),
                "position": int(priority.get("position", 0)),
                "is_default": bool(priority.get("is_default", False)),
                "active": bool(priority.get("active", True)),
            }
        )
        raw_rows.append(
            {
                "entity_type": "issue_priority",
                "entity_id": str(priority_id),
                "endpoint": "/enumerations/issue_priorities.json",
                "project_id": None,
                "updated_on": None,
                "fetched_at": context.fetched_at,
                "payload": priority,
            }
        )

    summary["issue_priorities_synced"] += await context.repo.upsert_issue_priorities(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_issues(context: SyncContext, summary: dict[str, Any]) -> None:
    scope = _project_scope(context.effective_project_ids)
    cursor = await _get_or_create_cursor(context.session, entity_type="issues", scope=scope)
    updated_since = _cursor_lower_bound(cursor.last_seen_updated_on, context.overlap_minutes)
    max_seen_updated_on = _normalize_datetime(cursor.last_seen_updated_on)

    issue_rows: list[dict[str, Any]] = []
    custom_field_rows: list[dict[str, Any]] = []
    journal_rows: list[dict[str, Any]] = []
    relation_rows: list[dict[str, Any]] = []
    watcher_rows: list[dict[str, Any]] = []
    attachment_rows: list[dict[str, Any]] = []
    raw_issue_rows: list[dict[str, Any]] = []
    raw_journal_rows: list[dict[str, Any]] = []
    raw_entity_rows: list[dict[str, Any]] = []

    async for issues in _iter_paginated(
        lambda limit, offset: context.client.get_issues(
            updated_since=updated_since,
            project_ids=context.effective_project_ids,
            limit=limit,
            offset=offset,
        ),
        payload_key="issues",
    ):
        for issue in issues:
            issue_id = int(issue["id"])
            project_ref = issue.get("project") or {}
            project_id = int(project_ref["id"])
            updated_on = _parse_datetime(issue.get("updated_on"))
            created_on = _parse_datetime(issue.get("created_on")) or context.fetched_at
            closed_on = _parse_datetime(issue.get("closed_on"))
            tracker_ref = issue.get("tracker") or {}
            status_ref = issue.get("status") or {}
            priority_ref = issue.get("priority") or {}
            author_ref = issue.get("author") or {}
            assigned_to_ref = issue.get("assigned_to") or {}

            if updated_on is not None and (
                max_seen_updated_on is None or updated_on > max_seen_updated_on
            ):
                max_seen_updated_on = updated_on

            custom_fields = list(issue.get("custom_fields", []))
            for custom_field in custom_fields:
                custom_field_id = _to_int_or_none(custom_field.get("id"))
                custom_field_name = _to_str_or_none(custom_field.get("name"))
                if custom_field_id is None or custom_field_name is None:
                    continue
                custom_field_rows.append(
                    {
                        "id": custom_field_id,
                        "name": custom_field_name,
                        "field_format": None,
                        "is_required": False,
                        "is_for_all": False,
                        "searchable": False,
                        "multiple": False,
                        "default_value": None,
                        "visible": True,
                        "roles_json": [],
                        "trackers_json": [],
                    }
                )

            issue_rows.append(
                {
                    "id": issue_id,
                    "project_id": project_id,
                    "tracker": _to_str_or_none(tracker_ref.get("name")),
                    "status": _to_str_or_none(status_ref.get("name")),
                    "priority": _to_str_or_none(priority_ref.get("name")),
                    "tracker_id": _to_int_or_none(tracker_ref.get("id")),
                    "status_id": _to_int_or_none(status_ref.get("id")),
                    "priority_id": _to_int_or_none(priority_ref.get("id")),
                    "category_id": _to_int_or_none((issue.get("category") or {}).get("id")),
                    "fixed_version_id": _to_int_or_none(
                        (issue.get("fixed_version") or {}).get("id")
                    ),
                    "subject": str(issue.get("subject", "")),
                    "description": _to_str_or_none(issue.get("description")),
                    "author_id": _to_int_or_none(author_ref.get("id")),
                    "assigned_to_id": _to_int_or_none(assigned_to_ref.get("id")),
                    "author": _to_str_or_none(author_ref.get("name")),
                    "assigned_to": _to_str_or_none(assigned_to_ref.get("name")),
                    "start_date": _parse_date(issue.get("start_date")),
                    "due_date": _parse_date(issue.get("due_date")),
                    "done_ratio": _to_int_or_none(issue.get("done_ratio")),
                    "is_private": bool(issue.get("is_private", False)),
                    "estimated_hours": _to_float_or_none(issue.get("estimated_hours")),
                    "spent_hours": _to_float_or_none(issue.get("spent_hours")),
                    "created_on": created_on,
                    "updated_on": updated_on or created_on,
                    "closed_on": closed_on,
                    "custom_fields": _custom_fields_map(custom_fields),
                }
            )
            raw_issue_rows.append(
                {
                    "id": issue_id,
                    "project_id": project_id,
                    "updated_on": updated_on or created_on,
                    "fetched_at": context.fetched_at,
                    "payload": issue,
                }
            )
            raw_entity_rows.append(
                {
                    "entity_type": "issue",
                    "entity_id": str(issue_id),
                    "endpoint": "/issues.json",
                    "project_id": project_id,
                    "updated_on": updated_on,
                    "fetched_at": context.fetched_at,
                    "payload": issue,
                }
            )

            for journal in issue.get("journals", []):
                journal_id = int(journal["id"])
                created_on_journal = (
                    _parse_datetime(journal.get("created_on")) or context.fetched_at
                )
                details = list(journal.get("details", []))
                journal_rows.append(
                    {
                        "id": journal_id,
                        "issue_id": issue_id,
                        "user_id": _to_int_or_none((journal.get("user") or {}).get("id")),
                        "author": _to_str_or_none((journal.get("user") or {}).get("name")),
                        "notes": _to_str_or_none(journal.get("notes")),
                        "private_notes": bool(journal.get("private_notes", False)),
                        "created_on": created_on_journal,
                        "details": {"items": details},
                    }
                )
                raw_journal_rows.append(
                    {
                        "id": journal_id,
                        "issue_id": issue_id,
                        "created_on": created_on_journal,
                        "fetched_at": context.fetched_at,
                        "payload": journal,
                    }
                )
                raw_entity_rows.append(
                    {
                        "entity_type": "journal",
                        "entity_id": str(journal_id),
                        "endpoint": f"/issues/{issue_id}.json",
                        "project_id": project_id,
                        "updated_on": created_on_journal,
                        "fetched_at": context.fetched_at,
                        "payload": journal,
                    }
                )

            for relation in issue.get("relations", []):
                target_issue_id = _to_int_or_none(relation.get("issue_id"))
                relation_id = _to_int_or_none(relation.get("id"))
                if target_issue_id is None or relation_id is None:
                    continue
                relation_rows.append(
                    {
                        "id": relation_id,
                        "issue_from_id": issue_id,
                        "issue_to_id": target_issue_id,
                        "relation_type": str(relation.get("relation_type", "relates")),
                        "delay": _to_int_or_none(relation.get("delay")),
                    }
                )

            for watcher in issue.get("watchers", []):
                watcher_id = _to_int_or_none(watcher.get("id"))
                if watcher_id is None:
                    continue
                watcher_rows.append({"issue_id": issue_id, "user_id": watcher_id})

            for attachment in issue.get("attachments", []):
                attachment_id = int(attachment["id"])
                attachment_rows.append(
                    {
                        "id": attachment_id,
                        "container_type": "issue",
                        "container_id": str(issue_id),
                        "project_id": project_id,
                        "issue_id": issue_id,
                        "journal_id": None,
                        "wiki_page_id": None,
                        "time_entry_id": None,
                        "news_id": None,
                        "document_id": None,
                        "message_id": None,
                        "filename": str(attachment.get("filename", "")),
                        "filesize": _to_int_or_none(attachment.get("filesize")),
                        "content_type": _to_str_or_none(attachment.get("content_type")),
                        "description": _to_str_or_none(attachment.get("description")),
                        "content_url": _to_str_or_none(attachment.get("content_url")),
                        "downloads": _to_int_or_none(attachment.get("downloads")) or 0,
                        "author_id": _to_int_or_none((attachment.get("author") or {}).get("id")),
                        "created_on": _parse_datetime(attachment.get("created_on")),
                        "digest": _to_str_or_none(attachment.get("digest")),
                    }
                )
                raw_entity_rows.append(
                    {
                        "entity_type": "attachment",
                        "entity_id": str(attachment_id),
                        "endpoint": f"/issues/{issue_id}.json",
                        "project_id": project_id,
                        "updated_on": _parse_datetime(attachment.get("created_on")),
                        "fetched_at": context.fetched_at,
                        "payload": attachment,
                    }
                )

    summary["issues_synced"] += await context.repo.upsert_issues(issue_rows)
    summary["raw_issues_synced"] += await context.repo.upsert_raw_issues(raw_issue_rows)
    summary["custom_fields_synced"] += await context.repo.upsert_custom_fields(custom_field_rows)
    summary["journals_synced"] += await context.repo.upsert_journals(journal_rows)
    summary["raw_journals_synced"] += await context.repo.upsert_raw_journals(raw_journal_rows)
    summary["relations_synced"] += await context.repo.upsert_issue_relations(relation_rows)
    summary["watchers_synced"] += await context.repo.upsert_issue_watchers(watcher_rows)
    summary["attachments_synced"] += await context.repo.upsert_attachments(attachment_rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_entity_rows)

    cursor.last_seen_updated_on = max_seen_updated_on
    cursor.last_success_at = context.fetched_at
    cursor.error_message = None


async def _sync_time_entries(context: SyncContext, summary: dict[str, Any]) -> None:
    scope = _project_scope(context.effective_project_ids)
    cursor = await _get_or_create_cursor(context.session, entity_type="time_entries", scope=scope)
    updated_since = _cursor_lower_bound(cursor.last_seen_updated_on, context.overlap_minutes)
    max_seen_updated_on = _normalize_datetime(cursor.last_seen_updated_on)

    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    async for entries in _iter_paginated(
        lambda limit, offset: context.client.get_time_entries(
            updated_since=updated_since,
            project_ids=context.effective_project_ids,
            limit=limit,
            offset=offset,
        ),
        payload_key="time_entries",
    ):
        for entry in entries:
            entry_id = int(entry["id"])
            project_id = _to_int_or_none((entry.get("project") or {}).get("id"))
            if project_id is None:
                continue
            issue_id = _to_int_or_none((entry.get("issue") or {}).get("id"))
            user_id = _to_int_or_none((entry.get("user") or {}).get("id"))
            activity_id = _to_int_or_none((entry.get("activity") or {}).get("id"))
            updated_on = _parse_datetime(entry.get("updated_on"))
            created_on = _parse_datetime(entry.get("created_on"))
            if updated_on is not None and (
                max_seen_updated_on is None or updated_on > max_seen_updated_on
            ):
                max_seen_updated_on = updated_on

            rows.append(
                {
                    "id": entry_id,
                    "project_id": project_id,
                    "issue_id": issue_id,
                    "user_id": user_id,
                    "activity_id": activity_id,
                    "hours": _to_float_or_none(entry.get("hours")),
                    "comments": _to_str_or_none(entry.get("comments")),
                    "spent_on": _parse_date(entry.get("spent_on")),
                    "created_on": created_on,
                    "updated_on": updated_on,
                }
            )
            raw_rows.append(
                {
                    "entity_type": "time_entry",
                    "entity_id": str(entry_id),
                    "endpoint": "/time_entries.json",
                    "project_id": project_id,
                    "updated_on": updated_on,
                    "fetched_at": context.fetched_at,
                    "payload": entry,
                }
            )

    summary["time_entries_synced"] += await context.repo.upsert_time_entries(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)

    cursor.last_seen_updated_on = max_seen_updated_on
    cursor.last_success_at = context.fetched_at
    cursor.error_message = None


async def _sync_news(context: SyncContext, summary: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    async for items in _iter_paginated(
        lambda limit, offset: context.client.get_news(
            project_ids=context.effective_project_ids,
            limit=limit,
            offset=offset,
        ),
        payload_key="news",
    ):
        for item in items:
            news_id = int(item["id"])
            project_id = _to_int_or_none((item.get("project") or {}).get("id"))
            if project_id is None:
                continue
            row = {
                "id": news_id,
                "project_id": project_id,
                "title": str(item.get("title", "")),
                "summary": _to_str_or_none(item.get("summary")),
                "description": _to_str_or_none(item.get("description")),
                "author_id": _to_int_or_none((item.get("author") or {}).get("id")),
                "created_on": _parse_datetime(item.get("created_on")),
            }
            rows.append(row)
            raw_rows.append(
                {
                    "entity_type": "news",
                    "entity_id": str(news_id),
                    "endpoint": "/news.json",
                    "project_id": project_id,
                    "updated_on": _parse_datetime(item.get("created_on")),
                    "fetched_at": context.fetched_at,
                    "payload": item,
                }
            )

    summary["news_synced"] += await context.repo.upsert_news(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_documents(context: SyncContext, summary: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    async for items in _iter_paginated(
        lambda limit, offset: context.client.get_documents(
            project_ids=context.effective_project_ids,
            limit=limit,
            offset=offset,
        ),
        payload_key="documents",
    ):
        for item in items:
            document_id = int(item["id"])
            project_id = _to_int_or_none((item.get("project") or {}).get("id"))
            if project_id is None:
                continue
            rows.append(
                {
                    "id": document_id,
                    "project_id": project_id,
                    "category_id": _to_int_or_none((item.get("category") or {}).get("id")),
                    "title": str(item.get("title", "")),
                    "description": _to_str_or_none(item.get("description")),
                    "created_on": _parse_datetime(item.get("created_on")),
                }
            )
            raw_rows.append(
                {
                    "entity_type": "document",
                    "entity_id": str(document_id),
                    "endpoint": "/documents.json",
                    "project_id": project_id,
                    "updated_on": _parse_datetime(item.get("created_on")),
                    "fetched_at": context.fetched_at,
                    "payload": item,
                }
            )

    summary["documents_synced"] += await context.repo.upsert_documents(rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_files(context: SyncContext, summary: dict[str, Any]) -> None:
    raw_rows: list[dict[str, Any]] = []
    attachment_rows: list[dict[str, Any]] = []
    async for items in _iter_paginated(
        lambda limit, offset: context.client.get_files(
            project_ids=context.effective_project_ids,
            limit=limit,
            offset=offset,
        ),
        payload_key="files",
    ):
        for item in items:
            file_id = int(item["id"])
            project_id = _to_int_or_none((item.get("project") or {}).get("id"))
            if project_id is None:
                continue
            attachment_rows.append(
                {
                    "id": file_id,
                    "container_type": "file",
                    "container_id": str(file_id),
                    "project_id": project_id,
                    "issue_id": None,
                    "journal_id": None,
                    "wiki_page_id": None,
                    "time_entry_id": None,
                    "news_id": None,
                    "document_id": None,
                    "message_id": None,
                    "filename": str(item.get("filename", "")),
                    "filesize": _to_int_or_none(item.get("filesize")),
                    "content_type": _to_str_or_none(item.get("content_type")),
                    "description": _to_str_or_none(item.get("description")),
                    "content_url": _to_str_or_none(item.get("content_url")),
                    "downloads": 0,
                    "author_id": _to_int_or_none((item.get("author") or {}).get("id")),
                    "created_on": _parse_datetime(item.get("created_on")),
                    "digest": None,
                }
            )
            raw_rows.append(
                {
                    "entity_type": "file",
                    "entity_id": str(file_id),
                    "endpoint": "/files.json",
                    "project_id": project_id,
                    "updated_on": _parse_datetime(item.get("created_on")),
                    "fetched_at": context.fetched_at,
                    "payload": item,
                }
            )

    summary["files_synced"] += len(attachment_rows)
    summary["attachments_synced"] += await context.repo.upsert_attachments(attachment_rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_boards_and_messages(context: SyncContext, summary: dict[str, Any]) -> None:
    if not context.board_ids:
        summary["modules_skipped"].append({"module": "boards", "reason": "no_board_ids_configured"})
        return

    project_id = await _default_project_id(context)
    if project_id is None:
        summary["modules_skipped"].append({"module": "boards", "reason": "no_project_context"})
        return

    board_rows: list[dict[str, Any]] = []
    message_rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []

    for board_id in context.board_ids:
        topics_total = 0
        messages_seen = 0

        async def _fetch_topics(
            limit: int,
            offset: int,
            *,
            current_board_id: int = board_id,
        ) -> dict[str, Any]:
            return await context.client.get_board_topics(
                board_id=current_board_id,
                limit=limit,
                offset=offset,
            )

        async for topics in _iter_paginated(
            _fetch_topics,
            payload_key="messages",
        ):
            topics_total += len(topics)
            raw_rows.append(
                {
                    "entity_type": "board_topics",
                    "entity_id": str(board_id),
                    "endpoint": f"/boards/{board_id}/topics.json",
                    "project_id": project_id,
                    "updated_on": None,
                    "fetched_at": context.fetched_at,
                    "payload": {"messages": topics},
                }
            )
            for topic in topics:
                detail_payload = await context.client.get_message(int(topic["id"]))
                message = detail_payload["message"]
                board_ref = message.get("board") or {"id": board_id, "name": f"Board {board_id}"}
                replies = list(message.get("replies", []))
                messages_seen += 1 + len(replies)

                board_rows.append(
                    {
                        "id": int(board_ref["id"]),
                        "project_id": project_id,
                        "name": str(board_ref.get("name", f"Board {board_id}")),
                        "description": None,
                        "position": 0,
                        "topics_count": topics_total,
                        "messages_count": messages_seen,
                    }
                )

                root_id = int(message["id"])
                message_rows.append(
                    {
                        "id": root_id,
                        "board_id": int(board_ref["id"]),
                        "parent_id": None,
                        "author_id": _to_int_or_none((message.get("author") or {}).get("id")),
                        "subject": str(message.get("subject", "")),
                        "content": _to_str_or_none(message.get("content")),
                        "replies_count": len(replies),
                        "last_reply_id": _to_int_or_none(
                            (replies[-1] if replies else {}).get("id")
                        ),
                        "locked": bool(message.get("locked", False)),
                        "sticky": _to_int_or_none(message.get("sticky")) or 0,
                        "created_on": _parse_datetime(message.get("created_on")),
                        "updated_on": _parse_datetime(message.get("updated_on")),
                    }
                )
                raw_rows.append(
                    {
                        "entity_type": "message",
                        "entity_id": str(root_id),
                        "endpoint": f"/messages/{root_id}.json",
                        "project_id": project_id,
                        "updated_on": _parse_datetime(message.get("updated_on")),
                        "fetched_at": context.fetched_at,
                        "payload": message,
                    }
                )

                for reply in replies:
                    reply_id = int(reply["id"])
                    message_rows.append(
                        {
                            "id": reply_id,
                            "board_id": int(board_ref["id"]),
                            "parent_id": root_id,
                            "author_id": _to_int_or_none((reply.get("author") or {}).get("id")),
                            "subject": str(reply.get("subject", "")),
                            "content": _to_str_or_none(reply.get("content")),
                            "replies_count": 0,
                            "last_reply_id": None,
                            "locked": False,
                            "sticky": 0,
                            "created_on": _parse_datetime(reply.get("created_on")),
                            "updated_on": _parse_datetime(reply.get("updated_on")),
                        }
                    )
                    raw_rows.append(
                        {
                            "entity_type": "message",
                            "entity_id": str(reply_id),
                            "endpoint": f"/messages/{root_id}.json",
                            "project_id": project_id,
                            "updated_on": _parse_datetime(reply.get("updated_on")),
                            "fetched_at": context.fetched_at,
                            "payload": reply,
                        }
                    )

    summary["boards_synced"] += await context.repo.upsert_boards(board_rows)
    summary["messages_synced"] += await context.repo.upsert_messages(message_rows)
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_rows)


async def _sync_wiki(context: SyncContext, summary: dict[str, Any]) -> None:
    if not context.wiki_pages:
        summary["modules_skipped"].append({"module": "wiki", "reason": "no_wiki_pages_configured"})
        return

    wiki_versions_rows: list[dict[str, Any]] = []
    raw_entity_rows: list[dict[str, Any]] = []
    raw_wiki_count = 0

    for token in context.wiki_pages:
        parsed = _parse_wiki_token(token)
        if parsed is None:
            summary["modules_skipped"].append(
                {
                    "module": "wiki",
                    "reason": "invalid_wiki_page_reference",
                    "reference": token,
                }
            )
            continue
        project_ref, title = parsed
        project_id = await _resolve_project_id(context, project_ref)
        if project_id is None:
            summary["modules_skipped"].append(
                {
                    "module": "wiki",
                    "reason": "project_not_resolved",
                    "reference": token,
                }
            )
            continue

        payload = await context.client.get_wiki_page(project_ref, title)
        page = payload["wiki_page"]
        updated_on = _parse_datetime(page.get("updated_on")) or context.fetched_at
        wiki_url = f"{context.base_url}/projects/{project_ref}/wiki/{title}"
        page_id = await context.repo.upsert_wiki_page(
            project_id=project_id,
            project_identifier=None if project_ref.isdigit() else project_ref,
            title=title,
            content=str(page.get("text", "")),
            version=int(page.get("version", 1)),
            parent_title=_to_str_or_none((page.get("parent") or {}).get("title")),
            updated_on=updated_on,
            url=wiki_url,
        )
        wiki_versions_rows.append(
            {
                "wiki_page_id": page_id,
                "version": int(page.get("version", 1)),
                "author_id": _to_int_or_none((page.get("author") or {}).get("id")),
                "comments": _to_str_or_none(page.get("comments")),
                "text": _to_str_or_none(page.get("text")),
                "updated_on": updated_on,
            }
        )
        await context.repo.upsert_raw_wiki(
            project_id=project_id,
            title=title,
            updated_on=updated_on,
            fetched_at=context.fetched_at,
            payload=page,
        )
        raw_wiki_count += 1
        raw_entity_rows.append(
            {
                "entity_type": "wiki_page",
                "entity_id": f"{project_ref}:{title}",
                "endpoint": f"/projects/{project_ref}/wiki/{title}.json",
                "project_id": project_id,
                "updated_on": updated_on,
                "fetched_at": context.fetched_at,
                "payload": page,
            }
        )
        summary["wiki_pages_synced"] += 1

    summary["wiki_versions_synced"] += await context.repo.upsert_wiki_versions(wiki_versions_rows)
    summary["raw_wiki_synced"] += raw_wiki_count
    summary["raw_entities_synced"] += await context.repo.upsert_raw_entities(raw_entity_rows)


async def _iter_paginated(
    fetch_page: Callable[[int, int], Awaitable[dict[str, Any]]],
    *,
    payload_key: str,
    page_size: int = 100,
) -> AsyncIterator[list[dict[str, Any]]]:
    offset = 0
    while True:
        payload = await fetch_page(page_size, offset)
        items = list(payload.get(payload_key, []))
        yield items

        total_count = int(payload.get("total_count", len(items)))
        limit = int(payload.get("limit", page_size))
        if total_count == 0:
            break

        offset += max(limit, 1)
        if offset >= total_count:
            break


async def _get_or_create_sync_state(session: AsyncSession, *, key: str) -> SyncState:
    state = await session.scalar(select(SyncState).where(SyncState.key == key))
    if state is not None:
        return state

    state = SyncState(key=key, last_sync_at=None, last_success_at=None, last_error=None)
    session.add(state)
    await session.flush()
    return state


async def _get_or_create_cursor(
    session: AsyncSession,
    *,
    entity_type: str,
    scope: str,
) -> SyncCursor:
    cursor = await session.scalar(
        select(SyncCursor).where(
            SyncCursor.entity_type == entity_type,
            SyncCursor.project_scope == scope,
        )
    )
    if cursor is not None:
        return cursor

    cursor = SyncCursor(
        entity_type=entity_type,
        project_scope=scope,
        last_seen_updated_on=None,
        last_success_at=None,
        cursor_token=None,
        error_message=None,
    )
    session.add(cursor)
    await session.flush()
    return cursor


def _cursor_lower_bound(last_seen: datetime | None, overlap_minutes: int) -> datetime | None:
    if last_seen is None:
        return None
    normalized = _normalize_datetime(last_seen)
    if normalized is None:
        return None
    return normalized - timedelta(minutes=max(overlap_minutes, 0))


def _project_scope(project_ids: list[int]) -> str:
    if not project_ids:
        return "global"
    return ",".join(str(project_id) for project_id in sorted(project_ids))


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        return datetime.fromisoformat(normalized)
    return None


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.strip())
    return None


def _to_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return int(stripped)
    return None


def _to_float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)
    return None


def _to_str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _custom_fields_map(custom_fields: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field in custom_fields:
        name = _to_str_or_none(field.get("name"))
        if name is None:
            continue
        output[name] = field.get("value")
    return output


def _parse_wiki_token(token: str) -> tuple[str, str] | None:
    if ":" not in token:
        return None
    project_ref, title = token.split(":", 1)
    project_ref = project_ref.strip()
    title = title.strip()
    if not project_ref or not title:
        return None
    return project_ref, title


async def _resolve_project_id(context: SyncContext, project_ref: str) -> int | None:
    if project_ref.isdigit():
        return int(project_ref)

    project_id = await context.repo.find_project_id_by_identifier(project_ref)
    if project_id is not None:
        return project_id

    if context.effective_project_ids:
        return context.effective_project_ids[0]

    return await _default_project_id(context)


async def _default_project_id(context: SyncContext) -> int | None:
    if context.effective_project_ids:
        return context.effective_project_ids[0]
    project_id = await context.session.scalar(
        select(Project.id).order_by(Project.id.asc()).limit(1)
    )
    if project_id is None:
        return None
    return int(project_id)
