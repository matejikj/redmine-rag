from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response

from redmine_rag import __version__
from redmine_rag.api.router import router
from redmine_rag.core.config import get_settings
from redmine_rag.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.include_router(router)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FRONTEND_DIST_DIR = _REPO_ROOT / "frontend" / "dist"


def _resolve_dist_path(relative_path: str) -> Path | None:
    safe_path = relative_path.strip("/")
    candidate = (_FRONTEND_DIST_DIR / safe_path).resolve()
    if not str(candidate).startswith(str(_FRONTEND_DIST_DIR.resolve())):
        return None
    return candidate


@app.get("/app", response_model=None)
async def ui_index() -> Response:
    index_path = _FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "Frontend build missing. Run `cd frontend && npm install && npm run build` "
                    "and open /app again."
                )
            },
        )
    return FileResponse(index_path)


@app.get("/app/{relative_path:path}", response_model=None)
async def ui_assets_or_spa(relative_path: str) -> Response:
    index_path = _FRONTEND_DIST_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "Frontend build missing. Run `cd frontend && npm install && npm run build` "
                    "and open /app again."
                )
            },
        )

    candidate = _resolve_dist_path(relative_path)
    if candidate is not None and candidate.exists() and candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(index_path)
