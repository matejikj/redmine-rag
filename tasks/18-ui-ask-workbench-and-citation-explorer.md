# Task 18: UI Ask Workbench and Citation Explorer

## Goal

Deliver a user-friendly Ask interface with transparent citations and evidence navigation.

## Scope

- Build Ask workspace with query box, filter controls, and response panel.
- Display citations with source type, snippet, and deep links.
- Highlight claim-to-citation mapping in answer view.
- Add explain/debug mode for retrieval and LLM diagnostics.

## Deliverables

- Ask page wired to `POST /v1/ask`.
- Citation drawer with sortable/filterable evidence cards.
- Confidence and grounding indicators.
- Session history of recent queries (local persistence).

## Acceptance Criteria

- User can ask question, read answer, and inspect evidence in one flow.
- Citation links are actionable and correctly mapped to claims.
- Insufficient-evidence fallback is clearly communicated in UI.
- Page remains responsive for longer answers and larger citation sets.

## Quality Gates

- E2E tests for ask + citation exploration journey.
- Snapshot tests for markdown rendering and citation markers.
- Usability check with at least 5 realistic support questions.
