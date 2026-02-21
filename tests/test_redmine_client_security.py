from __future__ import annotations

from pathlib import Path

import pytest

from redmine_rag.core.config import get_settings
from redmine_rag.ingestion.redmine_client import RedmineClient


@pytest.fixture
def reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_redmine_client_blocks_non_https_non_localhost(
    monkeypatch: pytest.MonkeyPatch,
    reset_settings_cache: None,
) -> None:
    monkeypatch.setenv("REDMINE_BASE_URL", "http://redmine.example.com")
    monkeypatch.setenv("REDMINE_ALLOWED_HOSTS", "redmine.example.com")

    with pytest.raises(ValueError, match="non-HTTPS"):
        RedmineClient()


def test_redmine_client_blocks_host_outside_allowlist(
    monkeypatch: pytest.MonkeyPatch,
    reset_settings_cache: None,
) -> None:
    monkeypatch.setenv("REDMINE_BASE_URL", "https://redmine.example.com")
    monkeypatch.setenv("REDMINE_ALLOWED_HOSTS", "other.example.com")

    with pytest.raises(ValueError, match="REDMINE_ALLOWED_HOSTS"):
        RedmineClient()


def test_redmine_client_allows_localhost_http(
    monkeypatch: pytest.MonkeyPatch,
    reset_settings_cache: None,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("REDMINE_BASE_URL", "http://127.0.0.1:8081")
    monkeypatch.setenv("REDMINE_ALLOWED_HOSTS", "127.0.0.1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'dummy.db'}")

    client = RedmineClient()
    assert client is not None
