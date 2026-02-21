from __future__ import annotations

import logging
import re
from collections import Counter
from threading import Lock
from typing import Literal

GuardrailReason = Literal[
    "prompt_injection",
    "ungrounded_claim",
    "schema_violation",
    "unsafe_content",
]

_ALL_REASONS: tuple[GuardrailReason, ...] = (
    "prompt_injection",
    "ungrounded_claim",
    "schema_violation",
    "unsafe_content",
)

_PROMPT_INJECTION_PATTERNS = (
    re.compile(r"\bignore\b.{0,40}\b(previous|prior|all)\b.{0,40}\binstructions?\b", re.I),
    re.compile(r"\b(disregard|bypass|override)\b.{0,40}\b(instruction|guardrail|policy)\b", re.I),
    re.compile(r"\b(system prompt|developer message|jailbreak|dan mode)\b", re.I),
    re.compile(
        r"\b(reveal|leak|exfiltrat|dump|show)\b.{0,80}\b(api[_ -]?key|token|secret|password)\b",
        re.I,
    ),
)

_UNSAFE_CONTENT_PATTERNS = (
    re.compile(r"\b(drop table|delete from|truncate table|rm -rf|sudo)\b", re.I),
    re.compile(r"\b(exploit|backdoor|ransomware|credential stuffing)\b", re.I),
)

_REJECTION_COUNTER: Counter[str] = Counter()
_COUNTER_LOCK = Lock()
logger = logging.getLogger(__name__)


def detect_text_violation(text: str) -> GuardrailReason | None:
    if not text.strip():
        return None
    if any(pattern.search(text) for pattern in _PROMPT_INJECTION_PATTERNS):
        return "prompt_injection"
    if any(pattern.search(text) for pattern in _UNSAFE_CONTENT_PATTERNS):
        return "unsafe_content"
    return None


def record_guardrail_rejection(
    reason: GuardrailReason,
    *,
    context: str,
    detail: str | None = None,
) -> None:
    with _COUNTER_LOCK:
        _REJECTION_COUNTER[reason] += 1
    logger.warning(
        "Guardrail rejected LLM content",
        extra={
            "guardrail_reason": reason,
            "guardrail_context": context,
            "guardrail_detail": detail,
        },
    )


def guardrail_rejection_counters() -> dict[str, int]:
    with _COUNTER_LOCK:
        snapshot: dict[str, int] = {
            reason: int(_REJECTION_COUNTER.get(reason, 0)) for reason in _ALL_REASONS
        }
    return snapshot


def reset_guardrail_rejection_counters() -> None:
    with _COUNTER_LOCK:
        _REJECTION_COUNTER.clear()


def guardrail_fallback_message(reason: GuardrailReason) -> str:
    if reason == "prompt_injection":
        return (
            "Dotaz nebo generovaný obsah obsahoval nepovolené instrukce. "
            "Odpověď byla z bezpečnostních důvodů omezena na ověřené evidence."
        )
    if reason == "unsafe_content":
        return (
            "Byl detekován potenciálně nebezpečný obsah. "
            "Byla použita bezpečná fallback odpověď bez neověřených instrukcí."
        )
    if reason == "schema_violation":
        return (
            "LLM výstup nesplnil požadovaný strukturovaný kontrakt. "
            "Byla použita bezpečná fallback odpověď."
        )
    return (
        "LLM výstup nebyl dostatečně podložen dostupnými citacemi. "
        "Byla použita pouze ověřená evidence."
    )
