from __future__ import annotations

import pytest

from redmine_rag.api.schemas import AskFilters
from redmine_rag.core.config import Settings
from redmine_rag.services import query_planner
from redmine_rag.services.query_planner import build_retrieval_plan


@pytest.mark.asyncio
async def test_build_retrieval_plan_heuristic_provider() -> None:
    settings = Settings(
        retrieval_planner_enabled=True,
        retrieval_planner_max_expansions=2,
        llm_provider="mock",
    )
    plan, diagnostics = await build_retrieval_plan(
        query="OAuth incident rollback for project 1 tracker 2 status 3",
        base_filters=AskFilters(),
        settings=settings,
    )

    assert plan is not None
    assert diagnostics.planner_mode == "heuristic"
    assert diagnostics.planner_status == "applied"
    assert len(plan.expansions) <= 2
    assert plan.suggested_filters.project_ids == [1]
    assert plan.suggested_filters.tracker_ids == [2]
    assert plan.suggested_filters.status_ids == [3]


@pytest.mark.asyncio
async def test_build_retrieval_plan_invalid_llm_payload_returns_failed_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FakeRuntimeClient:
        async def generate(
            self,
            *,
            model: str,
            prompt: str,
            system_prompt: str | None,
            timeout_s: float,
            response_schema: dict[str, object] | None,
        ) -> str:
            del model, prompt, system_prompt, timeout_s, response_schema
            return "not-a-json-payload"

    monkeypatch.setattr(
        query_planner,
        "build_llm_runtime_client",
        lambda *args, **kwargs: _FakeRuntimeClient(),
    )
    monkeypatch.setattr(
        query_planner,
        "resolve_runtime_model",
        lambda _settings: "mistral:7b-instruct-v0.3-q4_K_M",
    )

    settings = Settings(
        retrieval_planner_enabled=True,
        llm_provider="ollama",
        ollama_model="mistral:7b-instruct-v0.3-q4_K_M",
    )
    plan, diagnostics = await build_retrieval_plan(
        query="incident query",
        base_filters=AskFilters(),
        settings=settings,
    )

    assert plan is None
    assert diagnostics.planner_mode == "llm"
    assert diagnostics.planner_status == "failed"
    assert diagnostics.error is not None


def test_parse_planner_payload_rejects_non_object() -> None:
    payload = query_planner._parse_planner_payload('["nope"]')
    assert payload is None
