from __future__ import annotations

import asyncio

import typer
import uvicorn

from redmine_rag.core.config import get_settings
from redmine_rag.core.logging import configure_logging
from redmine_rag.extraction.properties import extract_issue_properties
from redmine_rag.indexing.chunk_indexer import rebuild_chunk_index
from redmine_rag.ingestion.sync_pipeline import run_incremental_sync

app = typer.Typer(help="redmine-rag command line")
sync_app = typer.Typer(help="sync operations")
extract_app = typer.Typer(help="extraction operations")
index_app = typer.Typer(help="index operations")
app.add_typer(sync_app, name="sync")
app.add_typer(extract_app, name="extract")
app.add_typer(index_app, name="index")


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
    summary = asyncio.run(rebuild_chunk_index(base_url=settings.redmine_base_url))
    typer.echo(summary)


if __name__ == "__main__":
    app()
