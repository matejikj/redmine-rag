from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from redmine_rag.api.schemas import AskRequest, AskResponse, Citation
from redmine_rag.db.session import get_session_factory
from redmine_rag.services.citation_service import to_citations
from redmine_rag.services.retrieval_service import HybridRetrievalResult, hybrid_retrieve

logger = logging.getLogger(__name__)

_TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_MIN_CLAIM_CHARS = 24
_MAX_CLAIMS = 5
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


async def answer_question(payload: AskRequest) -> AskResponse:
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

    draft_claims = _build_grounded_claims(
        citations=citations,
        query=payload.query,
        max_claims=min(payload.top_k, _MAX_CLAIMS),
    )
    claims = _validate_claims(draft_claims, citations)

    logger.info(
        "Ask claim validation finished",
        extra={
            "draft_claims": len(draft_claims),
            "validated_claims": len(claims),
            "citations_count": len(citations),
            "used_chunk_ids": [chunk.id for chunk in chunks],
        },
    )

    if not claims:
        return _no_evidence_response()

    answer_markdown = _render_answer_markdown(
        claims=claims,
        retrieval=retrieval,
    )
    confidence = _estimate_confidence(
        validated_claims=len(claims),
        citations_count=len(citations),
        retrieval_mode=retrieval.diagnostics.mode,
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


def _estimate_confidence(
    *, validated_claims: int, citations_count: int, retrieval_mode: str
) -> float:
    mode_bonus = 0.08 if retrieval_mode == "hybrid" else 0.0
    base = 0.3 + min(0.4, 0.07 * validated_claims) + min(0.15, 0.02 * citations_count) + mode_bonus
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
