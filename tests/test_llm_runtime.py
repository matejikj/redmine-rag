from __future__ import annotations

import httpx
import orjson
import pytest

from redmine_rag.services.llm_runtime import (
    OllamaRuntimeClient,
    probe_ollama_runtime,
    resolve_runtime_model,
)


@pytest.mark.asyncio
async def test_ollama_runtime_generate_success() -> None:
    captured_payload: dict[str, object] = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = dict(orjson.loads(request.content))
        return httpx.Response(
            status_code=200,
            json={"response": '{"topic":"oauth","confidence":0.8}'},
        )

    client = OllamaRuntimeClient(
        base_url="http://127.0.0.1:11434",
        max_concurrency=2,
        transport=httpx.MockTransport(_handler),
    )
    output = await client.generate(
        model="mistral:7b-instruct-v0.3-q4_K_M",
        prompt="issue context",
        system_prompt="return json",
        timeout_s=5.0,
        response_schema={"type": "object"},
    )

    assert output == '{"topic":"oauth","confidence":0.8}'
    assert captured_payload["model"] == "mistral:7b-instruct-v0.3-q4_K_M"
    assert captured_payload["prompt"] == "issue context"
    assert captured_payload["system"] == "return json"
    assert captured_payload["stream"] is False
    assert captured_payload["format"] == {"type": "object"}


@pytest.mark.asyncio
async def test_ollama_runtime_generate_timeout_maps_to_timeout_error() -> None:
    def _handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    client = OllamaRuntimeClient(
        base_url="http://127.0.0.1:11434",
        max_concurrency=1,
        transport=httpx.MockTransport(_handler),
    )
    with pytest.raises(TimeoutError, match="timed out"):
        await client.generate(
            model="x",
            prompt="y",
            system_prompt=None,
            timeout_s=0.5,
            response_schema=None,
        )


@pytest.mark.asyncio
async def test_ollama_probe_handles_connect_error() -> None:
    def _handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    probe = await probe_ollama_runtime(
        base_url="http://127.0.0.1:11434",
        model="mistral:7b-instruct-v0.3-q4_K_M",
        timeout_s=1.0,
        transport=httpx.MockTransport(_handler),
    )

    assert probe.provider == "ollama"
    assert probe.available is False
    assert probe.model_available is None
    assert "connection refused" in probe.detail


@pytest.mark.asyncio
async def test_ollama_probe_reports_model_availability() -> None:
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "models": [
                    {"name": "mistral:latest"},
                    {"name": "mistral:7b-instruct-v0.3-q4_K_M"},
                ]
            },
        )

    probe = await probe_ollama_runtime(
        base_url="http://127.0.0.1:11434",
        model="mistral:7b-instruct-v0.3-q4_K_M",
        timeout_s=1.0,
        transport=httpx.MockTransport(_handler),
    )

    assert probe.available is True
    assert probe.model_available is True
    assert "available" in probe.detail


def test_resolve_runtime_model_prefers_ollama_model_for_ollama_provider() -> None:
    from redmine_rag.core.config import Settings

    settings = Settings(
        llm_provider="ollama",
        llm_model="gpt-5-mini",
        ollama_model="mistral:7b-instruct-v0.3-q4_K_M",
    )
    assert resolve_runtime_model(settings) == "mistral:7b-instruct-v0.3-q4_K_M"
