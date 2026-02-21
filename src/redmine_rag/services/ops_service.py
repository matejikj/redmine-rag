from __future__ import annotations

import json
import shutil
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sqlalchemy import func, select, text

from redmine_rag import __version__
from redmine_rag.api.schemas import HealthCheck, HealthResponse, SyncJobCounts
from redmine_rag.core.config import get_settings
from redmine_rag.db.models import SyncJob, SyncState
from redmine_rag.db.session import get_session_factory
from redmine_rag.services.llm_runtime import is_ollama_provider, probe_llm_runtime


async def get_health_status() -> HealthResponse:
    settings = get_settings()
    checks: list[HealthCheck] = []
    sync_counts = SyncJobCounts()
    hard_fail = False

    db_started = time.perf_counter()
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
            counts = (
                await session.execute(
                    select(SyncJob.status, func.count(SyncJob.id)).group_by(SyncJob.status)
                )
            ).all()
            for status, count in counts:
                normalized_status = str(status).strip().lower()
                if normalized_status == "queued":
                    sync_counts.queued = int(count)
                elif normalized_status == "running":
                    sync_counts.running = int(count)
                elif normalized_status == "finished":
                    sync_counts.finished = int(count)
                elif normalized_status == "failed":
                    sync_counts.failed = int(count)

            sync_state = await session.scalar(
                select(SyncState).where(SyncState.key == "redmine_incremental")
            )
            if sync_state is not None and sync_state.last_error:
                checks.append(
                    HealthCheck(
                        name="sync_state",
                        status="warn",
                        detail=f"Last sync error present: {sync_state.last_error}",
                    )
                )

        checks.append(
            HealthCheck(
                name="database",
                status="ok",
                detail="Database connection healthy",
                latency_ms=int((time.perf_counter() - db_started) * 1000),
            )
        )
    except Exception as exc:  # noqa: BLE001
        hard_fail = True
        checks.append(
            HealthCheck(
                name="database",
                status="fail",
                detail=f"Database probe failed: {exc}",
                latency_ms=int((time.perf_counter() - db_started) * 1000),
            )
        )

    parsed_url = urlparse(settings.redmine_base_url)
    redmine_host = (parsed_url.hostname or "").lower()
    production_mode = settings.app_env in {"prod", "production"}
    if production_mode and redmine_host not in set(settings.redmine_allowed_hosts):
        checks.append(
            HealthCheck(
                name="outbound_policy",
                status="warn",
                detail=(
                    f"Configured REDMINE_BASE_URL host {redmine_host!r} "
                    "not present in REDMINE_ALLOWED_HOSTS"
                ),
            )
        )
    else:
        checks.append(
            HealthCheck(
                name="outbound_policy",
                status="ok",
                detail=f"Outbound host policy active for {redmine_host or 'unknown'}",
            )
        )

    if production_mode and settings.redmine_api_key.strip() in {
        "replace_me",
        "changeme",
        "mock-api-key",
    }:
        checks.append(
            HealthCheck(
                name="secrets",
                status="warn",
                detail="REDMINE_API_KEY uses placeholder value",
            )
        )
    else:
        checks.append(HealthCheck(name="secrets", status="ok", detail="Redmine secret configured"))

    if sync_counts.failed > 0:
        checks.append(
            HealthCheck(
                name="sync_jobs",
                status="warn",
                detail=f"There are {sync_counts.failed} failed sync jobs",
            )
        )

    if not settings.llm_extract_enabled:
        checks.append(
            HealthCheck(
                name="llm_runtime",
                status="ok",
                detail="LLM extraction is disabled",
            )
        )
    elif settings.llm_provider.strip().lower() in {"mock", "heuristic", "test"}:
        checks.append(
            HealthCheck(
                name="llm_runtime",
                status="ok",
                detail=f"LLM provider '{settings.llm_provider}' is local deterministic mock",
            )
        )
    elif is_ollama_provider(settings.llm_provider):
        probe = await probe_llm_runtime(settings)
        if not probe.available:
            checks.append(
                HealthCheck(
                    name="llm_runtime",
                    status="warn",
                    detail=probe.detail,
                    latency_ms=probe.latency_ms,
                )
            )
        elif probe.model_available is False:
            checks.append(
                HealthCheck(
                    name="llm_runtime",
                    status="warn",
                    detail=probe.detail,
                    latency_ms=probe.latency_ms,
                )
            )
        else:
            checks.append(
                HealthCheck(
                    name="llm_runtime",
                    status="ok",
                    detail=probe.detail,
                    latency_ms=probe.latency_ms,
                )
            )
    else:
        checks.append(
            HealthCheck(
                name="llm_runtime",
                status="warn",
                detail=f"LLM provider '{settings.llm_provider}' has no runtime integration",
            )
        )

    status = "ok"
    if hard_fail:
        status = "fail"
    elif any(check.status == "warn" for check in checks):
        status = "degraded"

    return HealthResponse(
        status=status,
        app=settings.app_name,
        version=__version__,
        utc_time=datetime.now(UTC),
        checks=checks,
        sync_jobs=sync_counts,
    )


def create_state_backup(destination_dir: Path | None = None) -> dict[str, Any]:
    settings = get_settings()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_root = destination_dir or Path("backups")
    backup_dir = backup_root / f"snapshot-{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    db_source = resolve_sqlite_db_path(settings.database_url)
    db_target = backup_dir / "redmine_rag.db"
    copied_files: list[str] = []

    for source, target in (
        (db_source, db_target),
        (Path(settings.vector_index_path), backup_dir / "chunks.index"),
        (Path(settings.vector_meta_path), backup_dir / "chunks.meta.json"),
    ):
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied_files.append(str(target))

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "app_version": __version__,
        "database_url": settings.database_url,
        "vector_index_path": settings.vector_index_path,
        "vector_meta_path": settings.vector_meta_path,
        "files": copied_files,
    }
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "backup_dir": str(backup_dir),
        "files": copied_files,
        "manifest": str(backup_dir / "manifest.json"),
    }


def restore_state_backup(source_dir: Path, *, force: bool) -> dict[str, Any]:
    if not force:
        raise ValueError("Restore requires --force to avoid accidental overwrite")
    settings = get_settings()
    backup_dir = source_dir
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Backup manifest missing: {manifest_path}")

    db_target = resolve_sqlite_db_path(settings.database_url)
    index_target = Path(settings.vector_index_path)
    meta_target = Path(settings.vector_meta_path)

    restored: list[str] = []
    for source, target in (
        (backup_dir / "redmine_rag.db", db_target),
        (backup_dir / "chunks.index", index_target),
        (backup_dir / "chunks.meta.json", meta_target),
    ):
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            restored.append(str(target))

    return {"restored_files": restored, "source_dir": str(backup_dir)}


def run_sqlite_maintenance() -> dict[str, Any]:
    settings = get_settings()
    db_path = resolve_sqlite_db_path(settings.database_url)
    if not db_path.exists():
        raise ValueError(f"Database path not found: {db_path}")

    started = time.perf_counter()
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.execute("VACUUM;")
        conn.execute("ANALYZE;")
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {"database": str(db_path), "elapsed_ms": elapsed_ms}


def resolve_sqlite_db_path(database_url: str) -> Path:
    parsed = urlparse(database_url)
    if not parsed.scheme.startswith("sqlite"):
        raise ValueError("Backup/maintenance currently supports only sqlite database URLs")
    if ":///" not in database_url:
        raise ValueError("Invalid sqlite database URL")
    raw_path = database_url.split(":///", maxsplit=1)[1]
    if not raw_path:
        raise ValueError("Invalid sqlite database URL")
    return Path(raw_path).expanduser().resolve()
