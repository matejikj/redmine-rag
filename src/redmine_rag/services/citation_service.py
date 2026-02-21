from __future__ import annotations

from redmine_rag.api.schemas import Citation
from redmine_rag.services.retrieval_service import RetrievedChunk


def to_citations(chunks: list[RetrievedChunk], snippet_length: int = 220) -> list[Citation]:
    citations: list[Citation] = []
    for idx, chunk in enumerate(chunks, start=1):
        snippet = chunk.text.strip().replace("\n", " ")
        if len(snippet) > snippet_length:
            snippet = f"{snippet[:snippet_length - 3]}..."
        citations.append(
            Citation(
                id=idx,
                url=chunk.url,
                source_type=chunk.source_type,
                source_id=chunk.source_id,
                snippet=snippet,
            )
        )
    return citations
