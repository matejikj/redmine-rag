from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha1
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from redmine_rag.db.models import (
    Attachment,
    Board,
    DocChunk,
    Document,
    Issue,
    Journal,
    Message,
    News,
    TimeEntry,
    WikiPage,
)
from redmine_rag.db.session import get_session_factory
from redmine_rag.indexing.chunker import chunk_text


@dataclass(slots=True)
class ChunkStats:
    sources_reindexed: int = 0
    chunks_updated: int = 0


class ChunkIndexer:
    def __init__(
        self,
        session: AsyncSession,
        *,
        base_url: str,
        target_chars: int = 1200,
        overlap_chars: int = 150,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._target_chars = target_chars
        self._overlap_chars = overlap_chars

    async def rebuild_all(self) -> dict[str, int]:
        await self._session.execute(delete(DocChunk))
        stats = await self.refresh(since=None)
        return {
            "sources_reindexed": stats.sources_reindexed,
            "chunks_updated": stats.chunks_updated,
        }

    async def refresh(self, since: datetime | None) -> ChunkStats:
        stats = ChunkStats()
        await self._index_issues(since, stats)
        await self._index_journals(since, stats)
        await self._index_wiki_pages(since, stats)
        await self._index_attachments(since, stats)
        await self._index_news(since, stats)
        await self._index_documents(since, stats)
        await self._index_messages(since, stats)
        await self._index_time_entries(since, stats)
        return stats

    async def _index_issues(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = select(Issue).order_by(Issue.id.asc())
        if since is not None:
            stmt = stmt.where(Issue.updated_on >= since)

        for issue in (await self._session.execute(stmt)).scalars().all():
            sections = [
                f"Issue #{issue.id}",
                issue.subject,
                issue.description or "",
                _render_custom_fields(issue.custom_fields),
            ]
            text = "\n\n".join(section for section in sections if section.strip())
            url = f"{self._base_url}/issues/{issue.id}"
            chunk_count = await self._replace_source_chunks(
                source_type="issue",
                source_id=str(issue.id),
                project_id=issue.project_id,
                text=text,
                url=url,
                source_created_on=issue.created_on,
                source_updated_on=issue.updated_on,
                source_metadata={
                    "tracker_id": issue.tracker_id,
                    "status_id": issue.status_id,
                    "priority_id": issue.priority_id,
                },
                refs={"issue_id": issue.id},
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _index_journals(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = (
            select(Journal, Issue.project_id)
            .join(Issue, Issue.id == Journal.issue_id)
            .order_by(Journal.id.asc())
        )
        if since is not None:
            stmt = stmt.where(Journal.created_on >= since)

        for journal, project_id in (await self._session.execute(stmt)).all():
            sections = [
                f"Journal #{journal.id} on issue #{journal.issue_id}",
                journal.notes or "",
                _render_journal_details(journal.details),
            ]
            text = "\n\n".join(section for section in sections if section.strip())
            source_id = f"{journal.issue_id}#{journal.id}"
            url = f"{self._base_url}/issues/{journal.issue_id}#note-{journal.id}"
            chunk_count = await self._replace_source_chunks(
                source_type="journal",
                source_id=source_id,
                project_id=project_id,
                text=text,
                url=url,
                source_created_on=journal.created_on,
                source_updated_on=journal.created_on,
                source_metadata={
                    "issue_id": journal.issue_id,
                    "private_notes": journal.private_notes,
                },
                refs={"issue_id": journal.issue_id, "journal_id": journal.id},
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _index_wiki_pages(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = select(WikiPage).order_by(WikiPage.id.asc())
        if since is not None:
            stmt = stmt.where(WikiPage.updated_on >= since)

        for page in (await self._session.execute(stmt)).scalars().all():
            sections = [
                f"Wiki: {page.title}",
                page.content,
            ]
            text = "\n\n".join(section for section in sections if section.strip())
            source_id = f"{page.project_id}:{page.title}"
            chunk_count = await self._replace_source_chunks(
                source_type="wiki",
                source_id=source_id,
                project_id=page.project_id,
                text=text,
                url=page.url,
                source_created_on=page.created_at,
                source_updated_on=page.updated_on,
                source_metadata={"title": page.title, "version": page.version},
                refs={"wiki_page_id": page.id},
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _index_attachments(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = select(Attachment).order_by(Attachment.id.asc())
        if since is not None:
            stmt = stmt.where(Attachment.created_on >= since)

        for attachment in (await self._session.execute(stmt)).scalars().all():
            sections = [
                f"Attachment: {attachment.filename}",
                attachment.description or "",
                attachment.content_type or "",
            ]
            text = "\n\n".join(section for section in sections if section.strip())
            source_id = (
                f"{attachment.issue_id}#{attachment.id}"
                if attachment.issue_id is not None
                else str(attachment.id)
            )
            url = attachment.content_url or _attachment_fallback_url(
                base_url=self._base_url,
                issue_id=attachment.issue_id,
                attachment_id=attachment.id,
            )
            chunk_count = await self._replace_source_chunks(
                source_type="attachment",
                source_id=source_id,
                project_id=attachment.project_id,
                text=text,
                url=url,
                source_created_on=attachment.created_on,
                source_updated_on=attachment.created_on,
                source_metadata={"container_type": attachment.container_type},
                refs={
                    "issue_id": attachment.issue_id,
                    "journal_id": attachment.journal_id,
                    "wiki_page_id": attachment.wiki_page_id,
                    "attachment_id": attachment.id,
                },
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _index_news(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = select(News).order_by(News.id.asc())
        if since is not None:
            stmt = stmt.where(News.created_on >= since)

        for news in (await self._session.execute(stmt)).scalars().all():
            sections = [
                news.title,
                news.summary or "",
                news.description or "",
            ]
            text = "\n\n".join(section for section in sections if section.strip())
            chunk_count = await self._replace_source_chunks(
                source_type="news",
                source_id=str(news.id),
                project_id=news.project_id,
                text=text,
                url=f"{self._base_url}/news/{news.id}",
                source_created_on=news.created_on,
                source_updated_on=news.created_on,
                source_metadata={"title": news.title},
                refs={"news_id": news.id},
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _index_documents(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = select(Document).order_by(Document.id.asc())
        if since is not None:
            stmt = stmt.where(Document.created_on >= since)

        for document in (await self._session.execute(stmt)).scalars().all():
            sections = [document.title, document.description or ""]
            text = "\n\n".join(section for section in sections if section.strip())
            chunk_count = await self._replace_source_chunks(
                source_type="document",
                source_id=str(document.id),
                project_id=document.project_id,
                text=text,
                url=f"{self._base_url}/documents/{document.id}",
                source_created_on=document.created_on,
                source_updated_on=document.created_on,
                source_metadata={"title": document.title, "category_id": document.category_id},
                refs={"document_id": document.id},
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _index_messages(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = (
            select(Message, Board.project_id)
            .join(Board, Board.id == Message.board_id)
            .order_by(Message.id.asc())
        )
        if since is not None:
            stmt = stmt.where(Message.updated_on >= since)

        for message, project_id in (await self._session.execute(stmt)).all():
            sections = [
                message.subject,
                message.content or "",
            ]
            text = "\n\n".join(section for section in sections if section.strip())
            root_topic_id = message.parent_id or message.id
            url = f"{self._base_url}/boards/{message.board_id}/topics/{root_topic_id}"
            if message.parent_id is not None:
                url = f"{url}#message-{message.id}"
            chunk_count = await self._replace_source_chunks(
                source_type="message",
                source_id=str(message.id),
                project_id=project_id,
                text=text,
                url=url,
                source_created_on=message.created_on,
                source_updated_on=message.updated_on,
                source_metadata={
                    "board_id": message.board_id,
                    "parent_id": message.parent_id,
                    "locked": message.locked,
                },
                refs={"message_id": message.id},
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _index_time_entries(self, since: datetime | None, stats: ChunkStats) -> None:
        stmt = select(TimeEntry).order_by(TimeEntry.id.asc())
        if since is not None:
            stmt = stmt.where(TimeEntry.updated_on >= since)

        for entry in (await self._session.execute(stmt)).scalars().all():
            if not entry.comments:
                continue
            text = "\n\n".join(
                [
                    f"Time entry #{entry.id}",
                    entry.comments,
                ]
            )
            chunk_count = await self._replace_source_chunks(
                source_type="time_entry",
                source_id=str(entry.id),
                project_id=entry.project_id,
                text=text,
                url=f"{self._base_url}/time_entries/{entry.id}",
                source_created_on=entry.created_on,
                source_updated_on=entry.updated_on,
                source_metadata={"hours": entry.hours, "spent_on": str(entry.spent_on)},
                refs={"time_entry_id": entry.id, "issue_id": entry.issue_id},
            )
            stats.sources_reindexed += 1
            stats.chunks_updated += chunk_count

    async def _replace_source_chunks(
        self,
        *,
        source_type: str,
        source_id: str,
        project_id: int | None,
        text: str,
        url: str,
        source_created_on: datetime | None,
        source_updated_on: datetime | None,
        source_metadata: dict[str, Any],
        refs: dict[str, int | None],
    ) -> int:
        await self._session.execute(
            delete(DocChunk).where(
                DocChunk.source_type == source_type,
                DocChunk.source_id == source_id,
            )
        )

        chunks = chunk_text(
            text, target_chars=self._target_chars, overlap_chars=self._overlap_chars
        )
        if not chunks:
            return 0

        normalized_created = _normalize_datetime(source_created_on)
        normalized_updated = _normalize_datetime(source_updated_on)
        for index, chunk in enumerate(chunks):
            chunk_key = _build_chunk_key(source_type=source_type, source_id=source_id, index=index)
            self._session.add(
                DocChunk(
                    source_type=source_type,
                    source_id=source_id,
                    project_id=project_id,
                    issue_id=refs.get("issue_id"),
                    journal_id=refs.get("journal_id"),
                    wiki_page_id=refs.get("wiki_page_id"),
                    attachment_id=refs.get("attachment_id"),
                    time_entry_id=refs.get("time_entry_id"),
                    news_id=refs.get("news_id"),
                    document_id=refs.get("document_id"),
                    message_id=refs.get("message_id"),
                    chunk_index=index,
                    text=chunk,
                    url=url,
                    source_created_on=normalized_created,
                    source_updated_on=normalized_updated,
                    source_metadata=source_metadata,
                    embedding_key=chunk_key,
                )
            )
        return len(chunks)


async def rebuild_chunk_index(
    *, base_url: str, target_chars: int = 1200, overlap_chars: int = 150
) -> dict[str, int]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        indexer = ChunkIndexer(
            session,
            base_url=base_url,
            target_chars=target_chars,
            overlap_chars=overlap_chars,
        )
        summary = await indexer.rebuild_all()
        await session.commit()
        return summary


def _render_custom_fields(custom_fields: dict[str, Any]) -> str:
    if not custom_fields:
        return ""
    lines = ["Custom fields:"]
    for key in sorted(custom_fields):
        lines.append(f"- {key}: {custom_fields[key]}")
    return "\n".join(lines)


def _render_journal_details(details_payload: dict[str, Any]) -> str:
    if not isinstance(details_payload, dict):
        return ""
    items = details_payload.get("items", [])
    if not items:
        return ""
    lines = ["Journal details:"]
    for item in items:
        name = item.get("name")
        old_value = item.get("old_value")
        new_value = item.get("new_value")
        lines.append(f"- {name}: {old_value} -> {new_value}")
    return "\n".join(lines)


def _attachment_fallback_url(base_url: str, issue_id: int | None, attachment_id: int) -> str:
    if issue_id is not None:
        return f"{base_url}/issues/{issue_id}"
    return f"{base_url}/attachments/{attachment_id}"


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _build_chunk_key(*, source_type: str, source_id: str, index: int) -> str:
    payload = f"{source_type}:{source_id}:{index}"
    return sha1(payload.encode("utf-8")).hexdigest()
