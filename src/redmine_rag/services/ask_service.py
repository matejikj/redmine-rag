from __future__ import annotations

from redmine_rag.api.schemas import AskRequest, AskResponse
from redmine_rag.db.session import get_session_factory
from redmine_rag.services.citation_service import to_citations
from redmine_rag.services.retrieval_service import hybrid_retrieve


async def answer_question(payload: AskRequest) -> AskResponse:
    session_factory = get_session_factory()
    async with session_factory() as session:
        chunks = await hybrid_retrieve(session, payload.query, payload.filters, payload.top_k)

    if not chunks:
        return AskResponse(
            answer_markdown=(
                "V dostupných datech jsem nenašel dostatečnou oporu pro tento dotaz. "
                "Zkus upravit filtr projektu/období nebo použít přesnější název feature."
            ),
            citations=[],
            used_chunk_ids=[],
            confidence=0.0,
        )

    citations = to_citations(chunks)
    lines: list[str] = ["### Shrnutí na základě Redmine zdrojů", ""]

    for citation in citations[: min(5, len(citations))]:
        lines.append(f"- Zdroj {citation.id}: pravděpodobně relevantní vlastnosti jsou popsány v [{citation.source_type} #{citation.source_id}]({citation.url}).")

    lines.append("")
    lines.append("Další detail je potřeba potvrdit po doplnění extrakce vlastností (`/v1/extract/properties`).")

    return AskResponse(
        answer_markdown="\n".join(lines),
        citations=citations,
        used_chunk_ids=[chunk.id for chunk in chunks],
        confidence=min(0.95, 0.45 + 0.05 * len(chunks)),
    )
