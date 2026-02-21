"""initial schema

Revision ID: 20260221_0001
Revises:
Create Date: 2026-02-21 12:00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260221_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_entity",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("entity_type", "entity_id", "endpoint", name="uq_raw_entity_key"),
    )
    op.create_index("ix_raw_entity_entity_type", "raw_entity", ["entity_type"])
    op.create_index("ix_raw_entity_entity_id", "raw_entity", ["entity_id"])
    op.create_index("ix_raw_entity_project_id", "raw_entity", ["project_id"])
    op.create_index("ix_raw_entity_updated_on", "raw_entity", ["updated_on"])

    op.create_table(
        "raw_issue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_raw_issue_project_id", "raw_issue", ["project_id"])
    op.create_index("ix_raw_issue_updated_on", "raw_issue", ["updated_on"])

    op.create_table(
        "raw_journal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_raw_journal_issue_id", "raw_journal", ["issue_id"])
    op.create_index("ix_raw_journal_created_on", "raw_journal", ["created_on"])

    op.create_table(
        "raw_wiki",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_raw_wiki_project_id", "raw_wiki", ["project_id"])
    op.create_index("ix_raw_wiki_title", "raw_wiki", ["title"])

    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identifier", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("homepage", sa.String(length=1024), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("identifier", name="uq_project_identifier"),
    )
    op.create_index("ix_project_identifier", "project", ["identifier"])
    op.create_index("ix_project_name", "project", ["name"])
    op.create_index("ix_project_status", "project", ["status"])
    op.create_index("ix_project_parent_id", "project", ["parent_id"])
    op.create_index("ix_project_created_on", "project", ["created_on"])
    op.create_index("ix_project_updated_on", "project", ["updated_on"])

    op.create_table(
        "user_entity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("login", sa.String(length=255), nullable=False),
        sa.Column("firstname", sa.String(length=255), nullable=True),
        sa.Column("lastname", sa.String(length=255), nullable=True),
        sa.Column("mail", sa.String(length=255), nullable=True),
        sa.Column("admin", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_login_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("login", name="uq_user_entity_login"),
    )
    op.create_index("ix_user_entity_login", "user_entity", ["login"])
    op.create_index("ix_user_entity_mail", "user_entity", ["mail"])
    op.create_index("ix_user_entity_status", "user_entity", ["status"])

    op.create_table(
        "group_entity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("users_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_group_entity_name"),
    )
    op.create_index("ix_group_entity_name", "group_entity", ["name"])

    op.create_table(
        "membership",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("principal_type", sa.String(length=16), nullable=False),
        sa.Column("principal_id", sa.Integer(), nullable=False),
        sa.Column("roles_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_membership_project_id", "membership", ["project_id"])
    op.create_index("ix_membership_principal_type", "membership", ["principal_type"])
    op.create_index("ix_membership_principal_id", "membership", ["principal_id"])

    op.create_table(
        "tracker",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("default_status_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_tracker_name"),
    )
    op.create_index("ix_tracker_name", "tracker", ["name"])

    op.create_table(
        "issue_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_issue_status_name"),
    )
    op.create_index("ix_issue_status_name", "issue_status", ["name"])

    op.create_table(
        "issue_priority",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_issue_priority_name"),
    )
    op.create_index("ix_issue_priority_name", "issue_priority", ["name"])

    op.create_table(
        "issue_category",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "name", name="uq_issue_category_project_name"),
    )
    op.create_index("ix_issue_category_project_id", "issue_category", ["project_id"])
    op.create_index("ix_issue_category_name", "issue_category", ["name"])
    op.create_index("ix_issue_category_assigned_to_id", "issue_category", ["assigned_to_id"])

    op.create_table(
        "version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("sharing", sa.String(length=64), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("wiki_page_title", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "name", name="uq_version_project_name"),
    )
    op.create_index("ix_version_project_id", "version", ["project_id"])
    op.create_index("ix_version_name", "version", ["name"])

    op.create_table(
        "custom_field",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("field_format", sa.String(length=64), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_for_all", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("searchable", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("multiple", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("default_value", sa.Text(), nullable=True),
        sa.Column("visible", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("roles_json", sa.JSON(), nullable=False),
        sa.Column("trackers_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_custom_field_name", "custom_field", ["name"])

    op.create_table(
        "issue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("tracker", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.String(length=100), nullable=True),
        sa.Column("tracker_id", sa.Integer(), nullable=True),
        sa.Column("status_id", sa.Integer(), nullable=True),
        sa.Column("priority_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("fixed_version_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("done_ratio", sa.Integer(), nullable=True),
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("estimated_hours", sa.Float(), nullable=True),
        sa.Column("spent_hours", sa.Float(), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("custom_fields", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_issue_project_id", "issue", ["project_id"])
    op.create_index("ix_issue_tracker", "issue", ["tracker"])
    op.create_index("ix_issue_status", "issue", ["status"])
    op.create_index("ix_issue_created_on", "issue", ["created_on"])
    op.create_index("ix_issue_updated_on", "issue", ["updated_on"])
    op.create_index("ix_issue_tracker_id", "issue", ["tracker_id"])
    op.create_index("ix_issue_status_id", "issue", ["status_id"])
    op.create_index("ix_issue_priority_id", "issue", ["priority_id"])
    op.create_index("ix_issue_category_id", "issue", ["category_id"])
    op.create_index("ix_issue_fixed_version_id", "issue", ["fixed_version_id"])
    op.create_index("ix_issue_author_id", "issue", ["author_id"])
    op.create_index("ix_issue_assigned_to_id", "issue", ["assigned_to_id"])

    op.create_table(
        "journal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("private_notes", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_journal_issue_id", "journal", ["issue_id"])
    op.create_index("ix_journal_created_on", "journal", ["created_on"])
    op.create_index("ix_journal_user_id", "journal", ["user_id"])

    op.create_table(
        "issue_relation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_from_id", sa.Integer(), sa.ForeignKey("issue.id"), nullable=False),
        sa.Column("issue_to_id", sa.Integer(), sa.ForeignKey("issue.id"), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("delay", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "issue_from_id", "issue_to_id", "relation_type", name="uq_issue_relation_pair"
        ),
    )
    op.create_index("ix_issue_relation_issue_from_id", "issue_relation", ["issue_from_id"])
    op.create_index("ix_issue_relation_issue_to_id", "issue_relation", ["issue_to_id"])
    op.create_index("ix_issue_relation_relation_type", "issue_relation", ["relation_type"])

    op.create_table(
        "issue_watcher",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_entity.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("issue_id", "user_id", name="uq_issue_watcher"),
    )
    op.create_index("ix_issue_watcher_issue_id", "issue_watcher", ["issue_id"])
    op.create_index("ix_issue_watcher_user_id", "issue_watcher", ["user_id"])

    op.create_table(
        "wiki_page",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("project_identifier", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("parent_title", sa.String(length=255), nullable=True),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "title", name="uq_wiki_page_project_title"),
    )
    op.create_index("ix_wiki_page_project_id", "wiki_page", ["project_id"])
    op.create_index("ix_wiki_page_project_identifier", "wiki_page", ["project_identifier"])
    op.create_index("ix_wiki_page_title", "wiki_page", ["title"])
    op.create_index("ix_wiki_page_updated_on", "wiki_page", ["updated_on"])

    op.create_table(
        "wiki_version",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("wiki_page_id", sa.Integer(), sa.ForeignKey("wiki_page.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("wiki_page_id", "version", name="uq_wiki_version"),
    )
    op.create_index("ix_wiki_version_wiki_page_id", "wiki_version", ["wiki_page_id"])
    op.create_index("ix_wiki_version_author_id", "wiki_version", ["author_id"])
    op.create_index("ix_wiki_version_updated_on", "wiki_version", ["updated_on"])

    op.create_table(
        "time_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user_entity.id"), nullable=True),
        sa.Column("activity_id", sa.Integer(), nullable=True),
        sa.Column("hours", sa.Float(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("spent_on", sa.Date(), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_time_entry_project_id", "time_entry", ["project_id"])
    op.create_index("ix_time_entry_issue_id", "time_entry", ["issue_id"])
    op.create_index("ix_time_entry_user_id", "time_entry", ["user_id"])
    op.create_index("ix_time_entry_activity_id", "time_entry", ["activity_id"])
    op.create_index("ix_time_entry_spent_on", "time_entry", ["spent_on"])
    op.create_index("ix_time_entry_updated_on", "time_entry", ["updated_on"])

    op.create_table(
        "attachment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("container_type", sa.String(length=32), nullable=False),
        sa.Column("container_id", sa.String(length=128), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("issue_id", sa.Integer(), nullable=True),
        sa.Column("journal_id", sa.Integer(), nullable=True),
        sa.Column("wiki_page_id", sa.Integer(), nullable=True),
        sa.Column("time_entry_id", sa.Integer(), nullable=True),
        sa.Column("news_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("filesize", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_url", sa.String(length=1024), nullable=True),
        sa.Column("downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("digest", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_attachment_container_type", "attachment", ["container_type"])
    op.create_index("ix_attachment_container_id", "attachment", ["container_id"])
    op.create_index("ix_attachment_project_id", "attachment", ["project_id"])
    op.create_index("ix_attachment_issue_id", "attachment", ["issue_id"])
    op.create_index("ix_attachment_journal_id", "attachment", ["journal_id"])
    op.create_index("ix_attachment_wiki_page_id", "attachment", ["wiki_page_id"])
    op.create_index("ix_attachment_time_entry_id", "attachment", ["time_entry_id"])
    op.create_index("ix_attachment_news_id", "attachment", ["news_id"])
    op.create_index("ix_attachment_document_id", "attachment", ["document_id"])
    op.create_index("ix_attachment_message_id", "attachment", ["message_id"])
    op.create_index("ix_attachment_author_id", "attachment", ["author_id"])
    op.create_index("ix_attachment_created_on", "attachment", ["created_on"])

    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_news_project_id", "news", ["project_id"])
    op.create_index("ix_news_title", "news", ["title"])
    op.create_index("ix_news_author_id", "news", ["author_id"])
    op.create_index("ix_news_created_on", "news", ["created_on"])

    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_document_project_id", "document", ["project_id"])
    op.create_index("ix_document_category_id", "document", ["category_id"])
    op.create_index("ix_document_title", "document", ["title"])
    op.create_index("ix_document_created_on", "document", ["created_on"])

    op.create_table(
        "board",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("project.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("topics_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_board_project_id", "board", ["project_id"])
    op.create_index("ix_board_name", "board", ["name"])

    op.create_table(
        "message",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("board_id", sa.Integer(), sa.ForeignKey("board.id"), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("replies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reply_id", sa.Integer(), nullable=True),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("sticky", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_message_board_id", "message", ["board_id"])
    op.create_index("ix_message_parent_id", "message", ["parent_id"])
    op.create_index("ix_message_author_id", "message", ["author_id"])
    op.create_index("ix_message_subject", "message", ["subject"])
    op.create_index("ix_message_created_on", "message", ["created_on"])
    op.create_index("ix_message_updated_on", "message", ["updated_on"])

    op.create_table(
        "custom_value",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customized_type", sa.String(length=64), nullable=False),
        sa.Column("customized_id", sa.String(length=128), nullable=False),
        sa.Column(
            "custom_field_id", sa.Integer(), sa.ForeignKey("custom_field.id"), nullable=False
        ),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_custom_value_customized_type", "custom_value", ["customized_type"])
    op.create_index("ix_custom_value_customized_id", "custom_value", ["customized_id"])
    op.create_index("ix_custom_value_custom_field_id", "custom_value", ["custom_field_id"])

    op.create_table(
        "doc_chunk",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("issue_id", sa.Integer(), nullable=True),
        sa.Column("journal_id", sa.Integer(), nullable=True),
        sa.Column("wiki_page_id", sa.Integer(), nullable=True),
        sa.Column("attachment_id", sa.Integer(), nullable=True),
        sa.Column("time_entry_id", sa.Integer(), nullable=True),
        sa.Column("news_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("source_created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.Column("embedding_key", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_type", "source_id", "chunk_index", name="uq_doc_chunk_source_idx"
        ),
        sa.UniqueConstraint("embedding_key", name="uq_doc_chunk_embedding_key"),
    )
    op.create_index("ix_doc_chunk_source_type", "doc_chunk", ["source_type"])
    op.create_index("ix_doc_chunk_source_id", "doc_chunk", ["source_id"])
    op.create_index("ix_doc_chunk_project_id", "doc_chunk", ["project_id"])
    op.create_index("ix_doc_chunk_issue_id", "doc_chunk", ["issue_id"])
    op.create_index("ix_doc_chunk_journal_id", "doc_chunk", ["journal_id"])
    op.create_index("ix_doc_chunk_wiki_page_id", "doc_chunk", ["wiki_page_id"])
    op.create_index("ix_doc_chunk_attachment_id", "doc_chunk", ["attachment_id"])
    op.create_index("ix_doc_chunk_time_entry_id", "doc_chunk", ["time_entry_id"])
    op.create_index("ix_doc_chunk_news_id", "doc_chunk", ["news_id"])
    op.create_index("ix_doc_chunk_document_id", "doc_chunk", ["document_id"])
    op.create_index("ix_doc_chunk_message_id", "doc_chunk", ["message_id"])
    op.create_index("ix_doc_chunk_source_updated_on", "doc_chunk", ["source_updated_on"])

    op.create_table(
        "issue_metric",
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), primary_key=True),
        sa.Column("first_response_s", sa.Integer(), nullable=True),
        sa.Column("resolution_s", sa.Integer(), nullable=True),
        sa.Column("reopen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("touch_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("handoff_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "issue_property",
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), primary_key=True),
        sa.Column("extractor_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("props_json", sa.JSON(), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_issue_property_extracted_at", "issue_property", ["extracted_at"])

    op.create_table(
        "sync_cursor",
        sa.Column("entity_type", sa.String(length=64), primary_key=True),
        sa.Column("project_scope", sa.String(length=64), primary_key=True, server_default="global"),
        sa.Column("last_seen_updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cursor_token", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "sync_state",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "sync_job",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_sync_job_status", "sync_job", ["status"])

    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunk_fts
        USING fts5(text, content='doc_chunk', content_rowid='id');
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS doc_chunk_ai AFTER INSERT ON doc_chunk BEGIN
            INSERT INTO doc_chunk_fts(rowid, text) VALUES (new.id, new.text);
        END;
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS doc_chunk_ad AFTER DELETE ON doc_chunk BEGIN
            INSERT INTO doc_chunk_fts(doc_chunk_fts, rowid, text) VALUES ('delete', old.id, old.text);
        END;
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS doc_chunk_au AFTER UPDATE ON doc_chunk BEGIN
            INSERT INTO doc_chunk_fts(doc_chunk_fts, rowid, text) VALUES ('delete', old.id, old.text);
            INSERT INTO doc_chunk_fts(rowid, text) VALUES (new.id, new.text);
        END;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS doc_chunk_au;")
    op.execute("DROP TRIGGER IF EXISTS doc_chunk_ad;")
    op.execute("DROP TRIGGER IF EXISTS doc_chunk_ai;")
    op.execute("DROP TABLE IF EXISTS doc_chunk_fts;")

    op.drop_index("ix_sync_job_status", table_name="sync_job")
    op.drop_table("sync_job")

    op.drop_table("sync_state")
    op.drop_table("sync_cursor")

    op.drop_index("ix_issue_property_extracted_at", table_name="issue_property")
    op.drop_table("issue_property")

    op.drop_table("issue_metric")

    op.drop_index("ix_doc_chunk_source_updated_on", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_message_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_document_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_news_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_time_entry_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_attachment_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_wiki_page_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_journal_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_issue_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_project_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_source_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_source_type", table_name="doc_chunk")
    op.drop_table("doc_chunk")

    op.drop_index("ix_custom_value_custom_field_id", table_name="custom_value")
    op.drop_index("ix_custom_value_customized_id", table_name="custom_value")
    op.drop_index("ix_custom_value_customized_type", table_name="custom_value")
    op.drop_table("custom_value")

    op.drop_index("ix_message_updated_on", table_name="message")
    op.drop_index("ix_message_created_on", table_name="message")
    op.drop_index("ix_message_subject", table_name="message")
    op.drop_index("ix_message_author_id", table_name="message")
    op.drop_index("ix_message_parent_id", table_name="message")
    op.drop_index("ix_message_board_id", table_name="message")
    op.drop_table("message")

    op.drop_index("ix_board_name", table_name="board")
    op.drop_index("ix_board_project_id", table_name="board")
    op.drop_table("board")

    op.drop_index("ix_document_created_on", table_name="document")
    op.drop_index("ix_document_title", table_name="document")
    op.drop_index("ix_document_category_id", table_name="document")
    op.drop_index("ix_document_project_id", table_name="document")
    op.drop_table("document")

    op.drop_index("ix_news_created_on", table_name="news")
    op.drop_index("ix_news_author_id", table_name="news")
    op.drop_index("ix_news_title", table_name="news")
    op.drop_index("ix_news_project_id", table_name="news")
    op.drop_table("news")

    op.drop_index("ix_attachment_created_on", table_name="attachment")
    op.drop_index("ix_attachment_author_id", table_name="attachment")
    op.drop_index("ix_attachment_message_id", table_name="attachment")
    op.drop_index("ix_attachment_document_id", table_name="attachment")
    op.drop_index("ix_attachment_news_id", table_name="attachment")
    op.drop_index("ix_attachment_time_entry_id", table_name="attachment")
    op.drop_index("ix_attachment_wiki_page_id", table_name="attachment")
    op.drop_index("ix_attachment_journal_id", table_name="attachment")
    op.drop_index("ix_attachment_issue_id", table_name="attachment")
    op.drop_index("ix_attachment_project_id", table_name="attachment")
    op.drop_index("ix_attachment_container_id", table_name="attachment")
    op.drop_index("ix_attachment_container_type", table_name="attachment")
    op.drop_table("attachment")

    op.drop_index("ix_time_entry_updated_on", table_name="time_entry")
    op.drop_index("ix_time_entry_spent_on", table_name="time_entry")
    op.drop_index("ix_time_entry_activity_id", table_name="time_entry")
    op.drop_index("ix_time_entry_user_id", table_name="time_entry")
    op.drop_index("ix_time_entry_issue_id", table_name="time_entry")
    op.drop_index("ix_time_entry_project_id", table_name="time_entry")
    op.drop_table("time_entry")

    op.drop_index("ix_wiki_version_updated_on", table_name="wiki_version")
    op.drop_index("ix_wiki_version_author_id", table_name="wiki_version")
    op.drop_index("ix_wiki_version_wiki_page_id", table_name="wiki_version")
    op.drop_table("wiki_version")

    op.drop_index("ix_wiki_page_updated_on", table_name="wiki_page")
    op.drop_index("ix_wiki_page_title", table_name="wiki_page")
    op.drop_index("ix_wiki_page_project_identifier", table_name="wiki_page")
    op.drop_index("ix_wiki_page_project_id", table_name="wiki_page")
    op.drop_table("wiki_page")

    op.drop_index("ix_issue_watcher_user_id", table_name="issue_watcher")
    op.drop_index("ix_issue_watcher_issue_id", table_name="issue_watcher")
    op.drop_table("issue_watcher")

    op.drop_index("ix_issue_relation_relation_type", table_name="issue_relation")
    op.drop_index("ix_issue_relation_issue_to_id", table_name="issue_relation")
    op.drop_index("ix_issue_relation_issue_from_id", table_name="issue_relation")
    op.drop_table("issue_relation")

    op.drop_index("ix_journal_user_id", table_name="journal")
    op.drop_index("ix_journal_created_on", table_name="journal")
    op.drop_index("ix_journal_issue_id", table_name="journal")
    op.drop_table("journal")

    op.drop_index("ix_issue_assigned_to_id", table_name="issue")
    op.drop_index("ix_issue_author_id", table_name="issue")
    op.drop_index("ix_issue_fixed_version_id", table_name="issue")
    op.drop_index("ix_issue_category_id", table_name="issue")
    op.drop_index("ix_issue_priority_id", table_name="issue")
    op.drop_index("ix_issue_status_id", table_name="issue")
    op.drop_index("ix_issue_tracker_id", table_name="issue")
    op.drop_index("ix_issue_updated_on", table_name="issue")
    op.drop_index("ix_issue_created_on", table_name="issue")
    op.drop_index("ix_issue_status", table_name="issue")
    op.drop_index("ix_issue_tracker", table_name="issue")
    op.drop_index("ix_issue_project_id", table_name="issue")
    op.drop_table("issue")

    op.drop_index("ix_custom_field_name", table_name="custom_field")
    op.drop_table("custom_field")

    op.drop_index("ix_version_name", table_name="version")
    op.drop_index("ix_version_project_id", table_name="version")
    op.drop_table("version")

    op.drop_index("ix_issue_category_assigned_to_id", table_name="issue_category")
    op.drop_index("ix_issue_category_name", table_name="issue_category")
    op.drop_index("ix_issue_category_project_id", table_name="issue_category")
    op.drop_table("issue_category")

    op.drop_index("ix_issue_priority_name", table_name="issue_priority")
    op.drop_table("issue_priority")

    op.drop_index("ix_issue_status_name", table_name="issue_status")
    op.drop_table("issue_status")

    op.drop_index("ix_tracker_name", table_name="tracker")
    op.drop_table("tracker")

    op.drop_index("ix_membership_principal_id", table_name="membership")
    op.drop_index("ix_membership_principal_type", table_name="membership")
    op.drop_index("ix_membership_project_id", table_name="membership")
    op.drop_table("membership")

    op.drop_index("ix_group_entity_name", table_name="group_entity")
    op.drop_table("group_entity")

    op.drop_index("ix_user_entity_status", table_name="user_entity")
    op.drop_index("ix_user_entity_mail", table_name="user_entity")
    op.drop_index("ix_user_entity_login", table_name="user_entity")
    op.drop_table("user_entity")

    op.drop_index("ix_project_updated_on", table_name="project")
    op.drop_index("ix_project_created_on", table_name="project")
    op.drop_index("ix_project_parent_id", table_name="project")
    op.drop_index("ix_project_status", table_name="project")
    op.drop_index("ix_project_name", table_name="project")
    op.drop_index("ix_project_identifier", table_name="project")
    op.drop_table("project")

    op.drop_index("ix_raw_wiki_title", table_name="raw_wiki")
    op.drop_index("ix_raw_wiki_project_id", table_name="raw_wiki")
    op.drop_table("raw_wiki")

    op.drop_index("ix_raw_journal_created_on", table_name="raw_journal")
    op.drop_index("ix_raw_journal_issue_id", table_name="raw_journal")
    op.drop_table("raw_journal")

    op.drop_index("ix_raw_issue_updated_on", table_name="raw_issue")
    op.drop_index("ix_raw_issue_project_id", table_name="raw_issue")
    op.drop_table("raw_issue")

    op.drop_index("ix_raw_entity_updated_on", table_name="raw_entity")
    op.drop_index("ix_raw_entity_project_id", table_name="raw_entity")
    op.drop_index("ix_raw_entity_entity_id", table_name="raw_entity")
    op.drop_index("ix_raw_entity_entity_type", table_name="raw_entity")
    op.drop_table("raw_entity")
