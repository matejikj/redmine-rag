from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from redmine_rag.db.base import Base, TimestampMixin


class RawIssue(Base, TimestampMixin):
    __tablename__ = "raw_issue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    updated_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)


class RawJournal(Base, TimestampMixin):
    __tablename__ = "raw_journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(Integer, index=True)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)


class RawWiki(Base, TimestampMixin):
    __tablename__ = "raw_wiki"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    updated_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)


class Issue(Base, TimestampMixin):
    __tablename__ = "issue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    tracker: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    priority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subject: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    closed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)

    journals: Mapped[list[Journal]] = relationship(back_populates="issue", cascade="all, delete-orphan")


class Journal(Base, TimestampMixin):
    __tablename__ = "journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issue.id"), index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    issue: Mapped[Issue] = relationship(back_populates="journals")


class WikiPage(Base, TimestampMixin):
    __tablename__ = "wiki_page"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    url: Mapped[str] = mapped_column(String(1024))


class DocChunk(Base, TimestampMixin):
    __tablename__ = "doc_chunk"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", "chunk_index", name="uq_doc_chunk_source_idx"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True)
    issue_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    journal_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1024))
    source_created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    embedding_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)


class IssueMetric(Base, TimestampMixin):
    __tablename__ = "issue_metric"

    issue_id: Mapped[int] = mapped_column(ForeignKey("issue.id"), primary_key=True)
    first_response_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)
    touch_count: Mapped[int] = mapped_column(Integer, default=0)
    handoff_count: Mapped[int] = mapped_column(Integer, default=0)


class IssueProperty(Base, TimestampMixin):
    __tablename__ = "issue_property"

    issue_id: Mapped[int] = mapped_column(ForeignKey("issue.id"), primary_key=True)
    extractor_version: Mapped[str] = mapped_column(String(32), default="v1")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    props_json: Mapped[dict] = mapped_column(JSON, default=dict)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class SyncState(Base, TimestampMixin):
    __tablename__ = "sync_state"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class SyncJob(Base, TimestampMixin):
    __tablename__ = "sync_job"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
