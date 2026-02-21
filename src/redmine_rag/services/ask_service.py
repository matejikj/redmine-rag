from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import orjson
from pydantic import BaseModel, Field, ValidationError, field_validator

from redmine_rag.api.schemas import AskRequest, AskResponse, Citation
from redmine_rag.core.config import get_settings
from redmine_rag.db.session import get_session_factory
from redmine_rag.services.citation_service import to_citations
from redmine_rag.services.llm_runtime import build_llm_runtime_client, resolve_runtime_model
from redmine_rag.services.retrieval_service import HybridRetrievalResult, hybrid_retrieve

logger = logging.getLogger(__name__)

_TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_MIN_CLAIM_CHARS = 24
_MAX_CLAIMS = 5
_MAX_CITATIONS_PER_CLAIM = 6
_STOPWORDS = {
    "a",
    "aby",
    "ale",
    "and",
    "bo",
    "by",
    "co",
    "do",
    "for",
    "i",
    "in",
    "is",
    "jak",
    "jaky",
    "jaké",
    "je",
    "jsou",
    "k",
    "na",
    "nebo",
    "o",
    "od",
    "po",
    "pro",
    "s",
    "se",
    "si",
    "the",
    "to",
    "u",
    "v",
    "ve",
    "z",
    "ze",
}


@dataclass(slots=True)
class GroundedClaim:
    text: str
    citation_ids: list[int]


@dataclass(slots=True)
class LlmGroundedAnswer:
    claims: list[GroundedClaim]
    limitations: str | None


class LlmClaimPayload(BaseModel):
    text: str = Field(min_length=8, max_length=600)
    citation_ids: list[int] = Field(min_length=1, max_length=_MAX_CITATIONS_PER_CLAIM)

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip().replace("\n", " ")
        return normalized

    @field_validator("citation_ids", mode="before")
    @classmethod
    def normalize_citation_ids(cls, value: object) -> list[int]:
        if not isinstance(value, list):
            return []
        normalized: list[int] = []
        seen: set[int] = set()
        for item in value:
            try:
                citation_id = int(item)
            except (TypeError, ValueError):
                continue
            if citation_id <= 0 or citation_id in seen:
                continue
            seen.add(citation_id)
            normalized.append(citation_id)
        return normalized


class LlmAnswerPayload(BaseModel):
    claims: list[LlmClaimPayload] = Field(default_factory=list, max_length=_MAX_CLAIMS)
    insufficient_evidence: bool = False
    limitations: str | None = Field(default=None, max_length=300)

    @field_validator("limitations")
    @classmethod
    def normalize_limitations(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().replace("\n", " ")
        return normalized or None


async def answer_question(payload: AskRequest) -> AskResponse:
    settings = get_settings()
    session_factory = get_session_factory()
    async with session_factory() as session:
        retrieval = await hybrid_retrieve(session, payload.query, payload.filters, payload.top_k)
        chunks = retrieval.chunks

    logger.info(
        "Ask retrieval completed",
        extra={
            "query": payload.query,
            "top_k": payload.top_k,
            "retrieval_mode": retrieval.diagnostics.mode,
            "lexical_candidates": retrieval.diagnostics.lexical_candidates,
            "vector_candidates": retrieval.diagnostics.vector_candidates,
            "fused_candidates": retrieval.diagnostics.fused_candidates,
            "used_chunk_ids": [chunk.id for chunk in chunks],
            "ask_answer_mode": settings.ask_answer_mode,
            "planner_mode": retrieval.diagnostics.planner_mode,
            "planner_status": retrieval.diagnostics.planner_status,
            "planner_latency_ms": retrieval.diagnostics.planner_latency_ms,
            "planner_normalized_query": retrieval.diagnostics.planner_normalized_query,
            "planner_expansions": retrieval.diagnostics.planner_expansions,
            "planner_confidence": retrieval.diagnostics.planner_confidence,
            "planner_queries": retrieval.diagnostics.planner_queries,
            "planner_filters_applied": retrieval.diagnostics.planner_filters_applied,
            "planner_error": retrieval.diagnostics.planner_error,
        },
    )

    if not chunks:
        return _no_evidence_response()

    citations = to_citations(chunks)
    if not _has_sufficient_evidence(payload.query, citations):
        logger.warning(
            "Ask rejected due to insufficient grounding evidence",
            extra={
                "query": payload.query,
                "retrieval_mode": retrieval.diagnostics.mode,
                "used_chunk_ids": [chunk.id for chunk in chunks],
            },
        )
        return _no_evidence_response()

    deterministic_draft_claims = _build_grounded_claims(
        citations=citations,
        query=payload.query,
        max_claims=min(payload.top_k, settings.ask_llm_max_claims, _MAX_CLAIMS),
    )
    deterministic_claims = _validate_claims(deterministic_draft_claims, citations)
    claims = deterministic_claims
    limitations: str | None = None
    synthesis_mode = "deterministic"

    if settings.ask_answer_mode == "llm_grounded":
        llm_answer = await _synthesize_llm_grounded_answer(
            query=payload.query,
            citations=citations,
            max_claims=min(payload.top_k, settings.ask_llm_max_claims, _MAX_CLAIMS),
            timeout_s=settings.ask_llm_timeout_s,
        )
        if llm_answer is not None and llm_answer.claims:
            claims = llm_answer.claims
            limitations = llm_answer.limitations
            synthesis_mode = "llm_grounded"
        else:
            synthesis_mode = "llm_fallback_deterministic"

    logger.info(
        "Ask claim validation finished",
        extra={
            "draft_claims": len(deterministic_draft_claims),
            "validated_claims": len(claims),
            "citations_count": len(citations),
            "used_chunk_ids": [chunk.id for chunk in chunks],
            "synthesis_mode": synthesis_mode,
            "planner_mode": retrieval.diagnostics.planner_mode,
            "planner_status": retrieval.diagnostics.planner_status,
            "planner_queries": retrieval.diagnostics.planner_queries,
        },
    )

    if not claims:
        return _no_evidence_response()

    answer_markdown = (
        _render_llm_answer_markdown(
            claims=claims,
            limitations=limitations,
            retrieval=retrieval,
        )
        if synthesis_mode == "llm_grounded"
        else _render_answer_markdown(
            claims=claims,
            retrieval=retrieval,
        )
    )
    confidence = _estimate_confidence(
        validated_claims=len(claims),
        citations_count=len(citations),
        retrieval_mode=retrieval.diagnostics.mode,
        llm_mode=(synthesis_mode == "llm_grounded"),
    )

    return AskResponse(
        answer_markdown=answer_markdown,
        citations=citations,
        used_chunk_ids=[chunk.id for chunk in chunks],
        confidence=confidence,
    )


def _no_evidence_response() -> AskResponse:
    return AskResponse(
        answer_markdown=(
            "Nemám dostatek důkazů v dostupných Redmine zdrojích pro spolehlivou odpověď. "
            "Uprav filtr projektu/období nebo polož přesnější dotaz na konkrétní issue/wiki."
        ),
        citations=[],
        used_chunk_ids=[],
        confidence=0.0,
    )


async def _synthesize_llm_grounded_answer(
    *,
    query: str,
    citations: list[Citation],
    max_claims: int,
    timeout_s: float,
) -> LlmGroundedAnswer | None:
    settings = get_settings()
    runtime_client = build_llm_runtime_client(provider=settings.llm_provider, settings=settings)
    model = resolve_runtime_model(settings)
    system_prompt = _load_ask_system_prompt()
    schema = _load_ask_schema()
    user_prompt = _build_ask_user_prompt(query=query, citations=citations, max_claims=max_claims)

    try:
        raw_response = await runtime_client.generate(
            model=model,
            prompt=user_prompt,
            system_prompt=system_prompt,
            timeout_s=timeout_s,
            response_schema=schema,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Ask LLM synthesis failed; falling back to deterministic renderer",
            extra={"error": str(exc), "provider": settings.llm_provider},
        )
        return None

    payload = _parse_ask_llm_payload(raw_response)
    if payload is None:
        return None
    if payload.insufficient_evidence:
        return LlmGroundedAnswer(claims=[], limitations=payload.limitations)

    draft_claims = [
        GroundedClaim(text=claim.text, citation_ids=claim.citation_ids)
        for claim in payload.claims[:max_claims]
    ]
    validated_claims = _validate_claims(draft_claims, citations)
    if not validated_claims:
        return None
    return LlmGroundedAnswer(claims=validated_claims, limitations=payload.limitations)


def _parse_ask_llm_payload(raw_response: str) -> LlmAnswerPayload | None:
    payload = raw_response.strip()
    if not payload:
        return None
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
            return None
        try:
            parsed = orjson.loads(payload[start : end + 1])
        except orjson.JSONDecodeError:
            return None
    if not isinstance(parsed, dict):
        return None
    try:
        return LlmAnswerPayload.model_validate(parsed)
    except ValidationError:
        return None


def _build_grounded_claims(
    *,
    citations: list[Citation],
    query: str,
    max_claims: int,
) -> list[GroundedClaim]:
    query_terms = _evidence_terms(query)
    claims: list[GroundedClaim] = []

    for citation in citations:
        sentence = _best_sentence(citation.snippet, query_terms)
        if len(sentence) < _MIN_CLAIM_CHARS:
            continue
        claims.append(
            GroundedClaim(
                text=sentence,
                citation_ids=[citation.id],
            )
        )
        if len(claims) >= max_claims:
            break

    return claims


def _validate_claims(claims: list[GroundedClaim], citations: list[Citation]) -> list[GroundedClaim]:
    allowed_ids = {citation.id for citation in citations}
    snippets_by_id = {citation.id: citation.snippet for citation in citations}
    validated: list[GroundedClaim] = []

    for claim in claims:
        citation_ids = sorted(
            {citation_id for citation_id in claim.citation_ids if citation_id in allowed_ids}
        )
        if not citation_ids:
            continue
        if not _claim_supported_by_snippets(claim.text, citation_ids, snippets_by_id):
            continue
        validated.append(GroundedClaim(text=claim.text, citation_ids=citation_ids))

    return validated


def _render_answer_markdown(
    *, claims: list[GroundedClaim], retrieval: HybridRetrievalResult
) -> str:
    lines: list[str] = [
        "### Odpověď podložená Redmine zdroji",
        "",
    ]

    for index, claim in enumerate(claims, start=1):
        marker = ", ".join(str(citation_id) for citation_id in claim.citation_ids)
        lines.append(f"{index}. {claim.text} [{marker}]")

    lines.extend(
        [
            "",
            "### Poznámka ke spolehlivosti",
            (
                "Pokud potřebuješ detail mimo uvedené citace, je nutné dohledat další "
                "evidence v Redmine datech."
            ),
            (
                f"_Retrieval mode: {retrieval.diagnostics.mode}; "
                f"lexical={retrieval.diagnostics.lexical_candidates}, "
                f"vector={retrieval.diagnostics.vector_candidates}, "
                f"fused={retrieval.diagnostics.fused_candidates}_"
            ),
        ]
    )
    return "\n".join(lines)


def _render_llm_answer_markdown(
    *,
    claims: list[GroundedClaim],
    limitations: str | None,
    retrieval: HybridRetrievalResult,
) -> str:
    lines: list[str] = [
        "### Odpověď podložená Redmine zdroji (LLM)",
        "",
    ]
    for index, claim in enumerate(claims, start=1):
        marker = ", ".join(str(citation_id) for citation_id in claim.citation_ids)
        lines.append(f"{index}. {claim.text} [{marker}]")

    if limitations:
        lines.extend(["", "### Omezení", limitations])

    lines.extend(
        [
            "",
            (
                f"_Retrieval mode: {retrieval.diagnostics.mode}; "
                f"lexical={retrieval.diagnostics.lexical_candidates}, "
                f"vector={retrieval.diagnostics.vector_candidates}, "
                f"fused={retrieval.diagnostics.fused_candidates}_"
            ),
        ]
    )
    return "\n".join(lines)


def _estimate_confidence(
    *,
    validated_claims: int,
    citations_count: int,
    retrieval_mode: str,
    llm_mode: bool = False,
) -> float:
    mode_bonus = 0.08 if retrieval_mode == "hybrid" else 0.0
    llm_bonus = 0.05 if llm_mode else 0.0
    base = (
        0.3
        + min(0.4, 0.07 * validated_claims)
        + min(0.15, 0.02 * citations_count)
        + mode_bonus
        + llm_bonus
    )
    return min(0.95, max(0.0, base))


def _has_sufficient_evidence(query: str, citations: list[Citation]) -> bool:
    query_terms = _evidence_terms(query)
    if not query_terms:
        return bool(citations)

    for citation in citations:
        snippet_terms = _evidence_terms(citation.snippet)
        if query_terms.intersection(snippet_terms):
            return True
    return False


def _claim_supported_by_snippets(
    claim_text: str,
    citation_ids: list[int],
    snippets_by_id: dict[int, str],
) -> bool:
    claim_terms = _evidence_terms(claim_text)
    if not claim_terms:
        return False

    for citation_id in citation_ids:
        snippet = snippets_by_id.get(citation_id, "")
        snippet_terms = _evidence_terms(snippet)
        if claim_terms.intersection(snippet_terms):
            return True
    return False


def _best_sentence(snippet: str, query_terms: set[str]) -> str:
    candidate_sentences = [
        sentence.strip().replace("\n", " ")
        for sentence in _SENTENCE_SPLIT_PATTERN.split(snippet)
        if sentence.strip()
    ]
    if not candidate_sentences:
        return snippet.strip().replace("\n", " ")

    if not query_terms:
        return candidate_sentences[0]

    def _score(sentence: str) -> tuple[int, int]:
        sentence_terms = _evidence_terms(sentence)
        return (len(query_terms.intersection(sentence_terms)), len(sentence))

    return max(candidate_sentences, key=_score)


def _evidence_terms(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if len(token) >= 2 and token not in _STOPWORDS
    }


def _load_ask_system_prompt() -> str:
    path = _repo_root() / "prompts" / "ask_system.md"
    return path.read_text(encoding="utf-8")


def _load_ask_schema() -> dict[str, Any]:
    path = _repo_root() / "prompts" / "ask_answer_schema.json"
    payload = orjson.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError("Ask answer schema must be a JSON object")
    return dict(payload)


def _build_ask_user_prompt(*, query: str, citations: list[Citation], max_claims: int) -> str:
    lines = [
        "User query:",
        query.strip(),
        "",
        f"Return up to {max_claims} grounded claims.",
        "Citations list:",
    ]
    for citation in citations:
        lines.append(
            f"[{citation.id}] source_type={citation.source_type}; "
            f"source_id={citation.source_id}; url={citation.url}; "
            f"snippet={citation.snippet}"
        )
    lines.append("")
    lines.append(
        "Use only citation IDs from the list above. "
        "If evidence is insufficient set insufficient_evidence=true."
    )
    return "\n".join(lines)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
