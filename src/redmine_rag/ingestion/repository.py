from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.db.models import (
    Attachment,
    Board,
    CustomField,
    Document,
    Group,
    Issue,
    IssuePriority,
    IssueRelation,
    IssueStatus,
    IssueWatcher,
    Journal,
    Message,
    News,
    Project,
    RawEntity,
    RawIssue,
    RawJournal,
    RawWiki,
    TimeEntry,
    Tracker,
    User,
    WikiPage,
    WikiVersion,
)


class IngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_raw_entities(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(
            RawEntity,
            rows,
            conflict_columns=("entity_type", "entity_id", "endpoint"),
        )

    async def upsert_raw_entity(self, row: dict[str, Any]) -> None:
        await self.upsert_raw_entities([row])

    async def upsert_raw_issues(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(RawIssue, rows, conflict_columns=("id",))

    async def upsert_raw_journals(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(RawJournal, rows, conflict_columns=("id",))

    async def upsert_raw_wiki(
        self,
        *,
        project_id: int,
        title: str,
        updated_on: datetime,
        fetched_at: datetime,
        payload: dict[str, Any],
    ) -> None:
        existing = await self._session.scalar(
            select(RawWiki).where(RawWiki.project_id == project_id, RawWiki.title == title)
        )
        if existing is None:
            self._session.add(
                RawWiki(
                    project_id=project_id,
                    title=title,
                    updated_on=updated_on,
                    fetched_at=fetched_at,
                    payload=payload,
                )
            )
            return

        existing.updated_on = updated_on
        existing.fetched_at = fetched_at
        existing.payload = payload

    async def upsert_projects(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Project, rows, conflict_columns=("id",))

    async def upsert_users(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(User, rows, conflict_columns=("id",))

    async def upsert_groups(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Group, rows, conflict_columns=("id",))

    async def upsert_trackers(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Tracker, rows, conflict_columns=("id",))

    async def upsert_issue_statuses(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(IssueStatus, rows, conflict_columns=("id",))

    async def upsert_issue_priorities(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(IssuePriority, rows, conflict_columns=("id",))

    async def upsert_custom_fields(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(CustomField, rows, conflict_columns=("id",))

    async def upsert_issues(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Issue, rows, conflict_columns=("id",))

    async def upsert_journals(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Journal, rows, conflict_columns=("id",))

    async def upsert_issue_relations(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(
            IssueRelation,
            rows,
            conflict_columns=("issue_from_id", "issue_to_id", "relation_type"),
        )

    async def upsert_issue_watchers(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(
            IssueWatcher,
            rows,
            conflict_columns=("issue_id", "user_id"),
        )

    async def upsert_attachments(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Attachment, rows, conflict_columns=("id",))

    async def upsert_time_entries(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(TimeEntry, rows, conflict_columns=("id",))

    async def upsert_news(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(News, rows, conflict_columns=("id",))

    async def upsert_documents(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Document, rows, conflict_columns=("id",))

    async def upsert_boards(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Board, rows, conflict_columns=("id",))

    async def upsert_messages(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(Message, rows, conflict_columns=("id",))

    async def upsert_wiki_page(
        self,
        *,
        project_id: int,
        project_identifier: str | None,
        title: str,
        content: str,
        version: int,
        parent_title: str | None,
        updated_on: datetime,
        url: str,
    ) -> int:
        existing = await self._session.scalar(
            select(WikiPage).where(WikiPage.project_id == project_id, WikiPage.title == title)
        )
        if existing is None:
            row = WikiPage(
                project_id=project_id,
                project_identifier=project_identifier,
                title=title,
                content=content,
                version=version,
                parent_title=parent_title,
                updated_on=updated_on,
                url=url,
            )
            self._session.add(row)
            await self._session.flush()
            return int(row.id)

        existing.project_identifier = project_identifier
        existing.content = content
        existing.version = version
        existing.parent_title = parent_title
        existing.updated_on = updated_on
        existing.url = url
        await self._session.flush()
        return int(existing.id)

    async def upsert_wiki_versions(self, rows: list[dict[str, Any]]) -> int:
        return await self._upsert_rows(
            WikiVersion, rows, conflict_columns=("wiki_page_id", "version")
        )

    async def find_project_id_by_identifier(self, identifier: str) -> int | None:
        project_id = await self._session.scalar(
            select(Project.id).where(Project.identifier == identifier)
        )
        if project_id is None:
            return None
        return int(project_id)

    async def _upsert_rows(
        self,
        model: type[Any],
        rows: list[dict[str, Any]],
        *,
        conflict_columns: tuple[str, ...],
    ) -> int:
        if not rows:
            return 0

        stmt = sqlite_insert(model).values(rows)
        set_columns: dict[str, Any] = {}
        for column in model.__table__.columns:
            if column.name in conflict_columns or column.name in {"id", "created_at", "updated_at"}:
                continue
            set_columns[column.name] = getattr(stmt.excluded, column.name)

        if set_columns:
            stmt = stmt.on_conflict_do_update(
                index_elements=list(conflict_columns),
                set_=set_columns,
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=list(conflict_columns))

        await self._session.execute(stmt)
        return len(rows)
