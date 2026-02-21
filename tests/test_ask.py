from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from redmine_rag.api.schemas import AskFilters, AskRequest
from redmine_rag.db.base import Base
from redmine_rag.db.session import get_engine, get_session_factory
from redmine_rag.main import app
from redmine_rag.services import ask_service
from redmine_rag.services.retrieval_service import (
    HybridRetrievalResult,
    RetrievalDiagnostics,
    RetrievedChunk,
)


def _mock_result(chunks: list[RetrievedChunk], *, mode: str = "hybrid") -> HybridRetrievalResult:
    return HybridRetrievalResult(
        chunks=chunks,
        diagnostics=RetrievalDiagnostics(
            mode=mode,
            lexical_candidates=len(chunks),
            vector_candidates=len(chunks),
            fused_candidates=len(chunks),
            lexical_weight=0.65,
            vector_weight=0.35,
            rrf_k=60,
        ),
    )


@pytest.fixture
async def isolated_ask_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "ask.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")

    from redmine_rag.core.config import get_settings

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    engine = get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def test_ask_returns_grounded_fallback_when_no_data(isolated_ask_env: None) -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/ask",
        json={
            "query": "Jaké vlastnosti má feature jednotné přihlášení?",
            "filters": {"project_ids": []},
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"answer_markdown", "citations", "used_chunk_ids", "confidence"}
    assert payload["citations"] == []
    assert payload["used_chunk_ids"] == []
    assert payload["confidence"] == 0.0
    assert "Nemám dostatek důkazů" in payload["answer_markdown"]


def test_ask_enforces_claim_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_hybrid_retrieve(*_args, **_kwargs) -> HybridRetrievalResult:
        return _mock_result(
            [
                RetrievedChunk(
                    id=101,
                    text="OAuth callback timeout on Safari login flow in SupportHub.",
                    url="http://x/issues/101",
                    source_type="issue",
                    source_id="101",
                    score=0.92,
                ),
                RetrievedChunk(
                    id=102,
                    text=(
                        "Runbook describes rollback and incident triage sequence "
                        "for auth incidents."
                    ),
                    url="http://x/wiki/Feature-Login",
                    source_type="wiki",
                    source_id="1:Feature-Login",
                    score=0.88,
                ),
            ]
        )

    monkeypatch.setattr(ask_service, "hybrid_retrieve", _fake_hybrid_retrieve)
    client = TestClient(app)

    response = client.post(
        "/v1/ask",
        json={
            "query": "Jaký je callback problém a jaký je rollback postup?",
            "filters": {"project_ids": [1]},
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["citations"]) == 2
    assert payload["used_chunk_ids"] == [101, 102]
    assert payload["confidence"] > 0.0

    claim_lines = [
        line for line in payload["answer_markdown"].splitlines() if re.match(r"^\d+\.\s", line)
    ]
    assert claim_lines
    for line in claim_lines:
        marker_match = re.search(r"\[(\d+(?:,\s*\d+)*)\]$", line)
        assert marker_match is not None
        for marker in marker_match.group(1).replace(" ", "").split(","):
            assert int(marker) in {citation["id"] for citation in payload["citations"]}


def test_ask_rejects_unsupported_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_hybrid_retrieve(*_args, **_kwargs) -> HybridRetrievalResult:
        return _mock_result(
            [
                RetrievedChunk(
                    id=301,
                    text="OAuth callback timeout and Safari cookie handling in login flow.",
                    url="http://x/issues/301",
                    source_type="issue",
                    source_id="301",
                    score=0.74,
                )
            ],
            mode="vector_only",
        )

    monkeypatch.setattr(ask_service, "hybrid_retrieve", _fake_hybrid_retrieve)
    client = TestClient(app)

    response = client.post(
        "/v1/ask",
        json={
            "query": "Jaká je daňová sazba v Německu pro digitální služby?",
            "filters": {"project_ids": [1]},
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"] == []
    assert payload["used_chunk_ids"] == []
    assert payload["confidence"] == 0.0
    assert "Nemám dostatek důkazů" in payload["answer_markdown"]


@pytest.mark.asyncio
async def test_ask_logs_retrieval_metadata(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def _fake_hybrid_retrieve(*_args, **_kwargs) -> HybridRetrievalResult:
        return _mock_result(
            [
                RetrievedChunk(
                    id=401,
                    text="Incident runbook covers rollback decision point for auth outages.",
                    url="http://x/wiki/Incident-Triage-Playbook",
                    source_type="wiki",
                    source_id="1:Incident-Triage-Playbook",
                    score=0.81,
                )
            ],
            mode="hybrid",
        )

    monkeypatch.setattr(ask_service, "hybrid_retrieve", _fake_hybrid_retrieve)
    caplog.set_level("INFO", logger="redmine_rag.services.ask_service")

    response = await ask_service.answer_question(
        AskRequest(
            query="Jaký je rollback postup při auth incidentu?",
            filters=AskFilters(project_ids=[1]),
            top_k=5,
        )
    )

    assert response.citations
    retrieval_log = next(
        record for record in caplog.records if record.message == "Ask retrieval completed"
    )
    assert retrieval_log.retrieval_mode == "hybrid"
    assert retrieval_log.used_chunk_ids == [401]

    validation_log = next(
        record for record in caplog.records if record.message == "Ask claim validation finished"
    )
    assert validation_log.validated_claims >= 1
