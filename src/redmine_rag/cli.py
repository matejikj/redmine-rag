from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer
import uvicorn

from redmine_rag.core.config import get_settings
from redmine_rag.core.logging import configure_logging
from redmine_rag.extraction.properties import extract_issue_properties
from redmine_rag.indexing.chunk_indexer import rebuild_chunk_index
from redmine_rag.indexing.embedding_indexer import refresh_embeddings
from redmine_rag.ingestion.sync_pipeline import run_incremental_sync
from redmine_rag.services.ops_service import (
    create_state_backup,
    restore_state_backup,
    run_sqlite_maintenance,
)

app = typer.Typer(help="redmine-rag command line")
sync_app = typer.Typer(help="sync operations")
extract_app = typer.Typer(help="extraction operations")
index_app = typer.Typer(help="index operations")
ops_app = typer.Typer(help="operations and maintenance")
app.add_typer(sync_app, name="sync")
app.add_typer(extract_app, name="extract")
app.add_typer(index_app, name="index")
app.add_typer(ops_app, name="ops")


@app.command("serve")
def serve(reload: bool = True) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    uvicorn.run(
        "redmine_rag.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=reload,
    )


@sync_app.command("run")
def sync_run(project_id: list[int] | None = typer.Option(None)) -> None:
    summary = asyncio.run(run_incremental_sync(project_ids=project_id or []))
    typer.echo(summary)


@extract_app.command("run")
def extract_run(issue_id: list[int] | None = typer.Option(None)) -> None:
    summary = asyncio.run(extract_issue_properties(issue_ids=issue_id))
    typer.echo(summary.model_dump())


@index_app.command("reindex")
def index_reindex() -> None:
    settings = get_settings()
    chunk_summary = asyncio.run(rebuild_chunk_index(base_url=settings.redmine_base_url))
    embedding_summary = asyncio.run(refresh_embeddings(since=None, full_rebuild=True))
    typer.echo({"chunks": chunk_summary, "embeddings": embedding_summary})


@index_app.command("embeddings")
def index_embeddings(
    full_rebuild: bool = typer.Option(False, "--full-rebuild"),
    since_minutes: int | None = typer.Option(None, "--since-minutes"),
) -> None:
    since = None
    if since_minutes is not None:
        since = datetime.now(UTC) - timedelta(minutes=max(since_minutes, 0))
    summary = asyncio.run(refresh_embeddings(since=since, full_rebuild=full_rebuild))
    typer.echo(summary)


@ops_app.command("backup")
def ops_backup(
    output_dir: str = typer.Option(
        "backups", "--output-dir", help="Backup destination root directory"
    ),
) -> None:
    summary = create_state_backup(destination_dir=Path(output_dir))
    typer.echo(summary)


@ops_app.command("restore")
def ops_restore(
    source_dir: str = typer.Option(..., "--source-dir", help="Backup snapshot directory"),
    force: bool = typer.Option(False, "--force", help="Allow overwrite of local DB/index files"),
) -> None:
    summary = restore_state_backup(source_dir=Path(source_dir), force=force)
    typer.echo(summary)


@ops_app.command("maintenance")
def ops_maintenance() -> None:
    summary = run_sqlite_maintenance()
    typer.echo(summary)


if __name__ == "__main__":
    app()
