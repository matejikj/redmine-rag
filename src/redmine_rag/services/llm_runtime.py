from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Protocol

import httpx

from redmine_rag.core.config import Settings, get_settings


@dataclass(slots=True, frozen=True)
class LlmRuntimeProbe:
    provider: str
    base_url: str | None
    model: str
    available: bool
    model_available: bool | None
    detail: str
    latency_ms: int | None


class LlmRuntimeClient(Protocol):
    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None,
        timeout_s: float,
        response_schema: dict[str, Any] | None,
    ) -> str: ...


class OllamaRuntimeClient:
    def __init__(
        self,
        *,
        base_url: str,
        max_concurrency: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._transport = transport

    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None,
        timeout_s: float,
        response_schema: dict[str, Any] | None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt is not None and system_prompt.strip():
            payload["system"] = system_prompt.strip()
        if response_schema is not None:
            payload["format"] = response_schema

        async with self._semaphore:
            try:
                async with httpx.AsyncClient(
                    base_url=self._base_url,
                    timeout=timeout_s,
                    transport=self._transport,
                ) as client:
                    response = await client.post("/api/generate", json=payload)
                    response.raise_for_status()
            except httpx.TimeoutException as exc:
                raise TimeoutError(f"Ollama request timed out after {timeout_s:.2f}s") from exc
            except httpx.RequestError as exc:
                raise RuntimeError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("Ollama response payload must be a JSON object")
        generated = data.get("response")
        if not isinstance(generated, str) or not generated.strip():
            raise RuntimeError("Ollama response missing non-empty 'response' field")
        return generated


class UnsupportedLlmRuntimeClient:
    def __init__(self, provider: str) -> None:
        self._provider = provider

    async def generate(
        self,
        *,
        model: str,
        prompt: str,
        system_prompt: str | None,
        timeout_s: float,
        response_schema: dict[str, Any] | None,
    ) -> str:
        del model, prompt, system_prompt, timeout_s, response_schema
        raise RuntimeError(f"LLM provider '{self._provider}' is not implemented")


def build_llm_runtime_client(
    provider: str,
    *,
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> LlmRuntimeClient:
    runtime_settings = settings or get_settings()
    normalized = provider.strip().lower()
    if normalized == "ollama":
        return OllamaRuntimeClient(
            base_url=runtime_settings.ollama_base_url,
            max_concurrency=runtime_settings.ollama_max_concurrency,
            transport=transport,
        )
    return UnsupportedLlmRuntimeClient(provider=normalized)


def is_ollama_provider(provider: str) -> bool:
    return provider.strip().lower() == "ollama"


def resolve_runtime_model(settings: Settings) -> str:
    if is_ollama_provider(settings.llm_provider):
        return settings.ollama_model
    return settings.llm_model


async def probe_llm_runtime(settings: Settings | None = None) -> LlmRuntimeProbe:
    runtime_settings = settings or get_settings()
    provider = runtime_settings.llm_provider.strip().lower()
    if provider != "ollama":
        return LlmRuntimeProbe(
            provider=provider,
            base_url=None,
            model=resolve_runtime_model(runtime_settings),
            available=True,
            model_available=True,
            detail=f"Provider '{provider}' has no runtime probe.",
            latency_ms=0,
        )
    return await probe_ollama_runtime(
        base_url=runtime_settings.ollama_base_url,
        model=runtime_settings.ollama_model,
        timeout_s=runtime_settings.ollama_timeout_s,
    )


async def probe_ollama_runtime(
    *,
    base_url: str,
    model: str,
    timeout_s: float,
    transport: httpx.AsyncBaseTransport | None = None,
) -> LlmRuntimeProbe:
    started = perf_counter()
    try:
        async with httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_s,
            transport=transport,
        ) as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException:
        latency_ms = int((perf_counter() - started) * 1000)
        return LlmRuntimeProbe(
            provider="ollama",
            base_url=base_url,
            model=model,
            available=False,
            model_available=None,
            detail=f"Ollama timeout after {timeout_s:.2f}s",
            latency_ms=latency_ms,
        )
    except httpx.RequestError as exc:
        latency_ms = int((perf_counter() - started) * 1000)
        return LlmRuntimeProbe(
            provider="ollama",
            base_url=base_url,
            model=model,
            available=False,
            model_available=None,
            detail=f"Ollama request failed: {exc}",
            latency_ms=latency_ms,
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((perf_counter() - started) * 1000)
        return LlmRuntimeProbe(
            provider="ollama",
            base_url=base_url,
            model=model,
            available=False,
            model_available=None,
            detail=f"Ollama probe failed: {exc}",
            latency_ms=latency_ms,
        )

    latency_ms = int((perf_counter() - started) * 1000)
    model_available = _is_model_present(payload=payload, expected_model=model)
    if model_available:
        detail = f"Ollama reachable and model '{model}' is available"
    else:
        detail = f"Ollama reachable, but model '{model}' is not listed in /api/tags"
    return LlmRuntimeProbe(
        provider="ollama",
        base_url=base_url,
        model=model,
        available=True,
        model_available=model_available,
        detail=detail,
        latency_ms=latency_ms,
    )


def _is_model_present(*, payload: object, expected_model: str) -> bool:
    if not isinstance(payload, dict):
        return False
    models = payload.get("models")
    if not isinstance(models, list):
        return False
    expected = expected_model.strip().lower()
    expected_base = expected.split(":", maxsplit=1)[0]
    for item in models:
        if not isinstance(item, dict):
            continue
        candidates = [item.get("name"), item.get("model")]
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            normalized = candidate.strip().lower()
            if normalized == expected:
                return True
            if normalized.split(":", maxsplit=1)[0] == expected_base:
                return True
    return False
