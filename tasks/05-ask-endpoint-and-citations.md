# Task 05: Ask Endpoint and Citation Enforcement

## Goal

Deliver reliable Q&A endpoint with strict grounding and citations.

## Scope

- Build `/v1/ask` orchestration for retrieval + answer generation.
- Enforce per-claim citations.
- Add graceful fallback when evidence is insufficient.

## Deliverables

- Prompt templates and answer schema.
- Citation builder with snippet + URL.
- Hallucination guardrails and post-validation.

## Acceptance Criteria

- Every factual claim maps to at least one citation.
- No-source cases return explicit "not enough evidence" response.
- Response format is stable for UI consumption.

## Quality Gates

- Contract tests for response schema.
- Red-team tests for unsupported claims.
- Logs include `used_chunk_ids` and retrieval metadata.
