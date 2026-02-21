from __future__ import annotations

import pytest

from redmine_rag.extraction.llm_structured import (
    ERROR_BUCKET_INVALID_JSON,
    ERROR_BUCKET_SCHEMA_VALIDATION,
    run_structured_extraction,
)


class _SequenceClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._index = 0

    async def extract(
        self,
        *,
        system_prompt: str,
        user_content: str,
        schema: dict[str, object],
        model: str,
        timeout_s: float,
    ) -> str:
        del system_prompt, user_content, schema, model, timeout_s
        response = self._responses[min(self._index, len(self._responses) - 1)]
        self._index += 1
        return response


@pytest.mark.asyncio
async def test_structured_extraction_retries_until_valid_payload() -> None:
    client = _SequenceClient(
        [
            "this is not valid json",
            (
                '{"topic":"oauth","module":"auth","problem_type":"timeout","root_cause":null,'
                '"resolution_type":"rollback","customer_impact":"high","risk_flags":["reopened"],'
                '"next_actions":["update runbook"],"confidence":0.82}'
            ),
        ]
    )
    result = await run_structured_extraction(
        client=client,
        system_prompt="x",
        user_content="y",
        schema={},
        model="gpt-5-mini",
        timeout_s=10,
        max_retries=2,
    )

    assert result.success is True
    assert result.attempts == 2
    assert result.error_bucket is None
    assert result.properties is not None
    assert result.properties.customer_impact == "high"


@pytest.mark.asyncio
async def test_structured_extraction_fails_on_schema_validation_after_retries() -> None:
    client = _SequenceClient(
        [
            (
                '{"topic":"oauth","module":"auth","problem_type":"timeout","root_cause":null,'
                '"resolution_type":"rollback","customer_impact":"critical","risk_flags":["reopened"],'
                '"next_actions":["update runbook"],"confidence":0.82}'
            ),
            (
                '{"topic":"oauth","module":"auth","problem_type":"timeout","root_cause":null,'
                '"resolution_type":"rollback","customer_impact":"critical","risk_flags":["reopened"],'
                '"next_actions":["update runbook"],"confidence":0.82}'
            ),
        ]
    )
    result = await run_structured_extraction(
        client=client,
        system_prompt="x",
        user_content="y",
        schema={},
        model="gpt-5-mini",
        timeout_s=10,
        max_retries=1,
    )

    assert result.success is False
    assert result.attempts == 2
    assert result.error_bucket == ERROR_BUCKET_SCHEMA_VALIDATION
    assert result.properties is None


@pytest.mark.asyncio
async def test_structured_extraction_tracks_invalid_json_bucket() -> None:
    client = _SequenceClient(["{invalid", "{still-invalid"])
    result = await run_structured_extraction(
        client=client,
        system_prompt="x",
        user_content="y",
        schema={},
        model="gpt-5-mini",
        timeout_s=10,
        max_retries=1,
    )

    assert result.success is False
    assert result.attempts == 2
    assert result.error_bucket == ERROR_BUCKET_INVALID_JSON
