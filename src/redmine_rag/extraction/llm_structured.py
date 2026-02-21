from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Protocol

import orjson
from pydantic import BaseModel, Field, ValidationError, field_validator

from redmine_rag.services.guardrail_service import (
    detect_text_violation,
    record_guardrail_rejection,
)
from redmine_rag.services.llm_runtime import LlmRuntimeClient, build_llm_runtime_client

PROMPT_VERSION = "extract_properties.v1"
SCHEMA_VERSION = "extract_properties.schema.v1"
LLM_EXTRACTOR_VERSION = "llm-json-v1"

ERROR_BUCKET_INVALID_JSON = "invalid_json"
ERROR_BUCKET_SCHEMA_VALIDATION = "schema_validation"
ERROR_BUCKET_TIMEOUT = "timeout"
ERROR_BUCKET_PROVIDER_ERROR = "provider_error"
ERROR_BUCKET_PROMPT_INJECTION = "prompt_injection"
ERROR_BUCKET_UNSAFE_CONTENT = "unsafe_content"


class StructuredExtractionClient(Protocol):
    async def extract(
        self,
        *,
        system_prompt: str,
        user_content: str,
        schema: dict[str, Any],
        model: str,
        timeout_s: float,
    ) -> str: ...


class LlmIssueProperties(BaseModel):
    topic: str | None
    module: str | None
    problem_type: str | None
    root_cause: str | None
    resolution_type: str | None
    customer_impact: Literal["low", "medium", "high"] | None
    risk_flags: list[str] = Field(default_factory=list, max_length=8)
    next_actions: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator(
        "topic",
        "module",
        "problem_type",
        "root_cause",
        "resolution_type",
        mode="before",
    )
    @classmethod
    def _normalize_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("risk_flags", "next_actions", mode="before")
    @classmethod
    def _normalize_list(cls, value: object) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        output: list[str] = []
        seen: set[str] = set()
        for item in value:
            normalized = str(item).strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            output.append(normalized)
        return output


@dataclass(slots=True)
class LlmExtractionResult:
    success: bool
    attempts: int
    error_bucket: str | None
    properties: LlmIssueProperties | None
    latency_ms: int
    last_error: str | None


class MockStructuredExtractionClient:
    async def extract(
        self,
        *,
        system_prompt: str,
        user_content: str,
        schema: dict[str, Any],
        model: str,
        timeout_s: float,
    ) -> str:
        del system_prompt, schema, model, timeout_s
        output = _heuristic_extract(user_content)
        return orjson.dumps(output).decode("utf-8")


class RuntimeStructuredExtractionClient:
    def __init__(self, runtime_client: LlmRuntimeClient) -> None:
        self._runtime_client = runtime_client

    async def extract(
        self,
        *,
        system_prompt: str,
        user_content: str,
        schema: dict[str, Any],
        model: str,
        timeout_s: float,
    ) -> str:
        return await self._runtime_client.generate(
            model=model,
            prompt=user_content,
            system_prompt=system_prompt,
            timeout_s=timeout_s,
            response_schema=schema,
        )


class UnsupportedStructuredExtractionClient:
    def __init__(self, provider: str) -> None:
        self._provider = provider

    async def extract(
        self,
        *,
        system_prompt: str,
        user_content: str,
        schema: dict[str, Any],
        model: str,
        timeout_s: float,
    ) -> str:
        del system_prompt, user_content, schema, model, timeout_s
        raise RuntimeError(f"LLM provider '{self._provider}' is not implemented for extraction")


def build_structured_extraction_client(provider: str) -> StructuredExtractionClient:
    normalized_provider = provider.strip().lower()
    if normalized_provider in {"mock", "heuristic", "test"}:
        return MockStructuredExtractionClient()
    if normalized_provider == "ollama":
        runtime_client = build_llm_runtime_client(provider=normalized_provider)
        return RuntimeStructuredExtractionClient(runtime_client=runtime_client)
    return UnsupportedStructuredExtractionClient(provider=normalized_provider)


async def run_structured_extraction(
    *,
    client: StructuredExtractionClient,
    system_prompt: str,
    user_content: str,
    schema: dict[str, Any],
    model: str,
    timeout_s: float,
    max_retries: int,
) -> LlmExtractionResult:
    attempts = 0
    error_bucket: str | None = None
    last_error: str | None = None
    started = perf_counter()

    for _ in range(max(max_retries, 0) + 1):
        attempts += 1
        try:
            raw_response = await client.extract(
                system_prompt=system_prompt,
                user_content=user_content,
                schema=schema,
                model=model,
                timeout_s=timeout_s,
            )
        except TimeoutError as exc:
            error_bucket = ERROR_BUCKET_TIMEOUT
            last_error = str(exc)
            continue
        except Exception as exc:  # noqa: BLE001
            error_bucket = ERROR_BUCKET_PROVIDER_ERROR
            last_error = str(exc)
            continue

        try:
            payload = parse_structured_payload(raw_response)
        except ValueError as exc:
            error_bucket = ERROR_BUCKET_INVALID_JSON
            last_error = str(exc)
            record_guardrail_rejection(
                "schema_violation",
                context="extract.llm_payload",
                detail=last_error[:180] if last_error else None,
            )
            continue

        try:
            properties = LlmIssueProperties.model_validate(payload)
        except ValidationError as exc:
            error_bucket = ERROR_BUCKET_SCHEMA_VALIDATION
            last_error = str(exc)
            record_guardrail_rejection(
                "schema_violation",
                context="extract.llm_payload",
                detail=last_error[:180] if last_error else None,
            )
            continue

        guardrail_reason = _detect_payload_violation(payload)
        if guardrail_reason is not None:
            error_bucket = guardrail_reason
            last_error = f"LLM payload rejected by guardrail: {guardrail_reason}"
            record_guardrail_rejection(
                guardrail_reason,
                context="extract.llm_payload",
                detail=last_error,
            )
            continue

        latency_ms = int((perf_counter() - started) * 1000)
        return LlmExtractionResult(
            success=True,
            attempts=attempts,
            error_bucket=None,
            properties=properties,
            latency_ms=latency_ms,
            last_error=None,
        )

    latency_ms = int((perf_counter() - started) * 1000)
    return LlmExtractionResult(
        success=False,
        attempts=attempts,
        error_bucket=error_bucket,
        properties=None,
        latency_ms=latency_ms,
        last_error=last_error,
    )


def parse_structured_payload(raw_response: str) -> dict[str, Any]:
    payload = raw_response.strip()
    if not payload:
        raise ValueError("Empty response payload")
    if payload.startswith("```"):
        payload = payload.strip("`").strip()
        if payload.lower().startswith("json"):
            payload = payload[4:].strip()
    try:
        parsed = orjson.loads(payload)
    except orjson.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start < 0 or end < 0 or end <= start:
            raise ValueError("Response is not valid JSON object") from None
        try:
            parsed = orjson.loads(payload[start : end + 1])
        except orjson.JSONDecodeError as exc:
            raise ValueError("Response is not valid JSON object") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Structured response must be a JSON object")
    return dict(parsed)


def load_structured_prompt() -> str:
    path = _repo_root() / "prompts" / "extract_properties_v1.md"
    return path.read_text(encoding="utf-8")


def load_structured_schema() -> dict[str, Any]:
    path = _repo_root() / "prompts" / "extract_properties_schema_v1.json"
    payload = orjson.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError("Structured extraction schema must be a JSON object")
    return dict(payload)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _heuristic_extract(content: str) -> dict[str, Any]:
    lowered = content.lower()
    topic = _find_first(lowered, ["oauth", "incident", "sla", "login", "rollback"])
    module = _find_first(lowered, ["auth", "identity", "billing", "support", "incident"])
    problem_type = _find_first(
        lowered,
        [
            "timeout",
            "regression",
            "outage",
            "latency",
            "permissions",
            "incident",
        ],
    )
    root_cause = _find_first(lowered, ["cookie", "callback", "misconfig", "race", "cache"])
    resolution_type = _find_first(
        lowered,
        ["rollback", "hotfix", "reconfigure", "restart", "runbook", "triage"],
    )
    customer_impact: Literal["low", "medium", "high"] | None = None
    if any(term in lowered for term in {"urgent", "major", "incident", "outage", "sev"}):
        customer_impact = "high"
    elif any(term in lowered for term in {"degrad", "slow", "latency", "retry"}):
        customer_impact = "medium"
    elif any(term in lowered for term in {"minor", "small"}):
        customer_impact = "low"

    risk_flags: list[str] = []
    if "reopen" in lowered:
        risk_flags.append("reopened")
    if "handoff" in lowered:
        risk_flags.append("handoff")
    if "private" in lowered:
        risk_flags.append("private_context")

    next_actions: list[str] = []
    if "runbook" in lowered:
        next_actions.append("update runbook")
    if "rca" in lowered or "root cause" in lowered:
        next_actions.append("complete rca")
    if not next_actions:
        next_actions.append("monitor issue")

    confidence = 0.55
    if topic is not None and problem_type is not None:
        confidence = 0.75
    if resolution_type is not None:
        confidence = min(0.92, confidence + 0.1)

    return {
        "topic": topic,
        "module": module,
        "problem_type": problem_type,
        "root_cause": root_cause,
        "resolution_type": resolution_type,
        "customer_impact": customer_impact,
        "risk_flags": risk_flags,
        "next_actions": next_actions,
        "confidence": confidence,
    }


def _find_first(text: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in text:
            return candidate
    return None


def _detect_payload_violation(
    payload: dict[str, Any],
) -> Literal["prompt_injection", "unsafe_content"] | None:
    for value in payload.values():
        for text in _iter_text_values(value):
            reason = detect_text_violation(text)
            if reason == "prompt_injection" or reason == "unsafe_content":
                return reason
    return None


def _iter_text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        list_output: list[str] = []
        for item in value:
            list_output.extend(_iter_text_values(item))
        return list_output
    if isinstance(value, dict):
        dict_output: list[str] = []
        for item in value.values():
            dict_output.extend(_iter_text_values(item))
        return dict_output
    return []
