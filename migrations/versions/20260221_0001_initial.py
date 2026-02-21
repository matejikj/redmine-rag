"""initial schema

Revision ID: 20260221_0001
Revises:
Create Date: 2026-02-21 12:00:00

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260221_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_issue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_raw_wiki_project_id", "raw_wiki", ["project_id"])
    op.create_index("ix_raw_wiki_title", "raw_wiki", ["title"])

    op.create_table(
        "issue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("tracker", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("priority", sa.String(length=100), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("assigned_to", sa.String(length=255), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("custom_fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_issue_project_id", "issue", ["project_id"])
    op.create_index("ix_issue_tracker", "issue", ["tracker"])
    op.create_index("ix_issue_status", "issue", ["status"])
    op.create_index("ix_issue_created_on", "issue", ["created_on"])
    op.create_index("ix_issue_updated_on", "issue", ["updated_on"])

    op.create_table(
        "journal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_journal_issue_id", "journal", ["issue_id"])
    op.create_index("ix_journal_created_on", "journal", ["created_on"])

    op.create_table(
        "wiki_page",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_on", sa.DateTime(timezone=True), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_wiki_page_project_id", "wiki_page", ["project_id"])
    op.create_index("ix_wiki_page_title", "wiki_page", ["title"])
    op.create_index("ix_wiki_page_updated_on", "wiki_page", ["updated_on"])

    op.create_table(
        "doc_chunk",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=True),
        sa.Column("journal_id", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("source_created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_updated_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedding_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("source_type", "source_id", "chunk_index", name="uq_doc_chunk_source_idx"),
        sa.UniqueConstraint("embedding_key", name="uq_doc_chunk_embedding_key"),
    )
    op.create_index("ix_doc_chunk_source_type", "doc_chunk", ["source_type"])
    op.create_index("ix_doc_chunk_source_id", "doc_chunk", ["source_id"])
    op.create_index("ix_doc_chunk_project_id", "doc_chunk", ["project_id"])
    op.create_index("ix_doc_chunk_issue_id", "doc_chunk", ["issue_id"])
    op.create_index("ix_doc_chunk_journal_id", "doc_chunk", ["journal_id"])
    op.create_index("ix_doc_chunk_source_updated_on", "doc_chunk", ["source_updated_on"])

    op.create_table(
        "issue_metric",
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), primary_key=True),
        sa.Column("first_response_s", sa.Integer(), nullable=True),
        sa.Column("resolution_s", sa.Integer(), nullable=True),
        sa.Column("reopen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("touch_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("handoff_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "issue_property",
        sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issue.id"), primary_key=True),
        sa.Column("extractor_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("props_json", sa.JSON(), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_issue_property_extracted_at", "issue_property", ["extracted_at"])

    op.create_table(
        "sync_state",
        sa.Column("key", sa.String(length=64), primary_key=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "sync_job",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
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

    op.drop_index("ix_issue_property_extracted_at", table_name="issue_property")
    op.drop_table("issue_property")

    op.drop_table("issue_metric")

    op.drop_index("ix_doc_chunk_source_updated_on", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_journal_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_issue_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_project_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_source_id", table_name="doc_chunk")
    op.drop_index("ix_doc_chunk_source_type", table_name="doc_chunk")
    op.drop_table("doc_chunk")

    op.drop_index("ix_wiki_page_updated_on", table_name="wiki_page")
    op.drop_index("ix_wiki_page_title", table_name="wiki_page")
    op.drop_index("ix_wiki_page_project_id", table_name="wiki_page")
    op.drop_table("wiki_page")

    op.drop_index("ix_journal_created_on", table_name="journal")
    op.drop_index("ix_journal_issue_id", table_name="journal")
    op.drop_table("journal")

    op.drop_index("ix_issue_updated_on", table_name="issue")
    op.drop_index("ix_issue_created_on", table_name="issue")
    op.drop_index("ix_issue_status", table_name="issue")
    op.drop_index("ix_issue_tracker", table_name="issue")
    op.drop_index("ix_issue_project_id", table_name="issue")
    op.drop_table("issue")

    op.drop_index("ix_raw_wiki_title", table_name="raw_wiki")
    op.drop_index("ix_raw_wiki_project_id", table_name="raw_wiki")
    op.drop_table("raw_wiki")

    op.drop_index("ix_raw_journal_created_on", table_name="raw_journal")
    op.drop_index("ix_raw_journal_issue_id", table_name="raw_journal")
    op.drop_table("raw_journal")

    op.drop_index("ix_raw_issue_updated_on", table_name="raw_issue")
    op.drop_index("ix_raw_issue_project_id", table_name="raw_issue")
    op.drop_table("raw_issue")
