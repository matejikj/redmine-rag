# SupportHub Knowledge Layer Blueprint (Data Task 6)

## Goal
Build a realistic knowledge layer (`wiki`, `news`, `documents`, `files`) that is tightly connected to issue narratives.

## Design Principles
- Every knowledge artifact should be traceable to concrete issue IDs.
- Content must reflect the same domain themes as issues (module, scenario family, risk).
- Knowledge artifacts should be naturally citable in RAG answers.

## Wiki Layer
- 20 generated wiki pages on top of base pages.
- Topic families:
  - SLA metrics
  - Evidence timeline
  - Root-cause catalog
  - Escalation policy
  - Citation quality checklist
- Each page includes:
  - revision version (`>=2` for generated pages)
  - references to primary + related issue IDs
  - parent linkage to core playbook pages

## News Layer
- Release updates, incident reviews, and process-change announcements.
- Every item references issue IDs and related wiki/document context.
- Content mirrors operational timeline and rollout/process governance updates.

## Documents Layer
- 18 generated documents organized by category.
- Focus areas:
  - release readiness
  - incident review
  - process change
  - knowledge remediation
- Each document references issue IDs and a corresponding wiki article.

## Files Layer
- 24 generated project files with realistic artifact types:
  - diagnostic logs
  - rollback checklists
  - evidence exports
  - timeline snapshots
  - postmortem notes
  - query plans
- File naming and description are tied to specific issue IDs.

## Acceptance Mapping
- Natural citation support: issue and wiki/document references are embedded in text fields.
- Topic consistency with issues: module/scenario/risk values are propagated from issues.
- No isolated content: each artifact points to issue context and related knowledge entities.
