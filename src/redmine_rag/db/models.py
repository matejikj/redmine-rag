from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from redmine_rag.db.base import Base, TimestampMixin


class RawEntity(Base, TimestampMixin):
    __tablename__ = "raw_entity"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "endpoint", name="uq_raw_entity_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str] = mapped_column(String(128), index=True)
    endpoint: Mapped[str] = mapped_column(String(255))
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload: Mapped[dict] = mapped_column(JSON)


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


class Project(Base, TimestampMixin):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identifier: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=1, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    homepage: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class User(Base, TimestampMixin):
    __tablename__ = "user_entity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    firstname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lastname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mail: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    admin: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[int] = mapped_column(Integer, default=1, index=True)
    last_login_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Group(Base, TimestampMixin):
    __tablename__ = "group_entity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    users_json: Mapped[list] = mapped_column(JSON, default=list)


class Membership(Base, TimestampMixin):
    __tablename__ = "membership"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    principal_type: Mapped[str] = mapped_column(String(16), index=True)
    principal_id: Mapped[int] = mapped_column(Integer, index=True)
    roles_json: Mapped[list] = mapped_column(JSON, default=list)


class Tracker(Base, TimestampMixin):
    __tablename__ = "tracker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    default_status_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class IssueStatus(Base, TimestampMixin):
    __tablename__ = "issue_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class IssuePriority(Base, TimestampMixin):
    __tablename__ = "issue_priority"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class IssueCategory(Base, TimestampMixin):
    __tablename__ = "issue_category"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_issue_category_project_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    assigned_to_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)


class Version(Base, TimestampMixin):
    __tablename__ = "version"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_version_project_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sharing: Mapped[str | None] = mapped_column(String(64), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    wiki_page_title: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Issue(Base, TimestampMixin):
    __tablename__ = "issue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    tracker: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    priority: Mapped[str | None] = mapped_column(String(100), nullable=True)

    tracker_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    priority_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    fixed_version_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    subject: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    assigned_to_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    done_ratio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    spent_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    closed_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)

    journals: Mapped[list[Journal]] = relationship(back_populates="issue", cascade="all, delete-orphan")


class Journal(Base, TimestampMixin):
    __tablename__ = "journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issue.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_notes: Mapped[bool] = mapped_column(Boolean, default=False)
    created_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    issue: Mapped[Issue] = relationship(back_populates="journals")


class IssueRelation(Base, TimestampMixin):
    __tablename__ = "issue_relation"
    __table_args__ = (
        UniqueConstraint("issue_from_id", "issue_to_id", "relation_type", name="uq_issue_relation_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_from_id: Mapped[int] = mapped_column(ForeignKey("issue.id"), index=True)
    issue_to_id: Mapped[int] = mapped_column(ForeignKey("issue.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(64), index=True)
    delay: Mapped[int | None] = mapped_column(Integer, nullable=True)


class IssueWatcher(Base, TimestampMixin):
    __tablename__ = "issue_watcher"
    __table_args__ = (UniqueConstraint("issue_id", "user_id", name="uq_issue_watcher"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issue.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_entity.id"), index=True)


class WikiPage(Base, TimestampMixin):
    __tablename__ = "wiki_page"
    __table_args__ = (UniqueConstraint("project_id", "title", name="uq_wiki_page_project_title"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    project_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    url: Mapped[str] = mapped_column(String(1024))


class WikiVersion(Base, TimestampMixin):
    __tablename__ = "wiki_version"
    __table_args__ = (UniqueConstraint("wiki_page_id", "version", name="uq_wiki_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wiki_page_id: Mapped[int] = mapped_column(ForeignKey("wiki_page.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class TimeEntry(Base, TimestampMixin):
    __tablename__ = "time_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    issue_id: Mapped[int | None] = mapped_column(ForeignKey("issue.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user_entity.id"), nullable=True, index=True)
    activity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    spent_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class Attachment(Base, TimestampMixin):
    __tablename__ = "attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    container_type: Mapped[str] = mapped_column(String(32), index=True)
    container_id: Mapped[str] = mapped_column(String(128), index=True)
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    issue_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    journal_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    wiki_page_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    time_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    news_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    message_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(512))
    filesize: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    digest: Mapped[str | None] = mapped_column(String(255), nullable=True)


class News(Base, TimestampMixin):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class Document(Base, TimestampMixin):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class Board(Base, TimestampMixin):
    __tablename__ = "board"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    topics_count: Mapped[int] = mapped_column(Integer, default=0)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)


class Message(Base, TimestampMixin):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("board.id"), index=True)
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    author_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    subject: Mapped[str] = mapped_column(String(512), index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    replies_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reply_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    sticky: Mapped[int] = mapped_column(Integer, default=0)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


class CustomField(Base, TimestampMixin):
    __tablename__ = "custom_field"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    field_format: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    is_for_all: Mapped[bool] = mapped_column(Boolean, default=False)
    searchable: Mapped[bool] = mapped_column(Boolean, default=False)
    multiple: Mapped[bool] = mapped_column(Boolean, default=False)
    default_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    roles_json: Mapped[list] = mapped_column(JSON, default=list)
    trackers_json: Mapped[list] = mapped_column(JSON, default=list)


class CustomValue(Base, TimestampMixin):
    __tablename__ = "custom_value"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customized_type: Mapped[str] = mapped_column(String(64), index=True)
    customized_id: Mapped[str] = mapped_column(String(128), index=True)
    custom_field_id: Mapped[int] = mapped_column(ForeignKey("custom_field.id"), index=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)


class DocChunk(Base, TimestampMixin):
    __tablename__ = "doc_chunk"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", "chunk_index", name="uq_doc_chunk_source_idx"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    issue_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    journal_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    wiki_page_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    attachment_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    time_entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    news_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    document_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    message_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1024))
    source_created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
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


class SyncCursor(Base, TimestampMixin):
    __tablename__ = "sync_cursor"

    entity_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_scope: Mapped[str] = mapped_column(String(64), primary_key=True, default="global")
    last_seen_updated_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cursor_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


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
