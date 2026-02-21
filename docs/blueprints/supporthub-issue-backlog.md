# SupportHub Issue Backlog Blueprint (Data Task 3)

## Goal
Create a realistic issue backlog for a single project (`platform-core`) that can validate retrieval, analytics, and citation behavior end-to-end.

## Backlog Shape
- Total backlog: 120+ issues (current dataset exceeds this threshold).
- Narrative unit: 5-issue story arc.
- Story arc composition:
  - `Epic`
  - `Feature`
  - `Bug`
  - `Support`
  - `Incident`

## Status Policy
Required status mix in dataset:
- `New`
- `In Progress`
- `Resolved`
- `Closed`
- `Reopened`

Rules:
- `Reopened` appears only for defect-heavy classes (`Bug`, `Incident`).
- `Resolved` and `Closed` can carry `closed_on` timestamp.

## Dependency Model
Dependencies are explicit and traceable in `relations`:
- `blocks`
- `relates`
- `duplicates`

Pattern:
- Feature usually blocks Epic completion.
- Bug relates to the Feature that introduced/contains the failure area.
- Support can duplicate a known Bug.
- Incident can block or duplicate Support case depending on escalation path.

## Edge Cases
Dataset must include deterministic edge cases:
- `Reopened` issue after false closure.
- `Stalled` issue with long-running blocker.
- `Mis-prioritized` issue (`priority=Low` while impact is high).

Each edge case is encoded by custom field:
- `Risk Flag`: `Reopened` / `Stalled` / `Mis-prioritized` / `None`

## Content Realism Requirements
Each issue contains:
- unique `subject`
- non-template `description` with account, channel, region, signal, root cause hypothesis, remediation, and prevention context
- metadata fields:
  - `Module`
  - `Customer Impact`
  - `Workflow Stage`
  - `Workstream`
  - `Customer Segment`
  - `Issue Class`
  - `Scenario Family`
  - `Risk Flag`
  - `Customer Account`

## Acceptance Mapping
- 120+ issues with realistic context: satisfied by generated story arcs.
- Mixed statuses including reopened: enforced by status policy and deterministic reopened cases.
- Real dependency links (`blocks`, `relates`, `duplicates`): enforced in relation generator.
- Edge cases present: encoded with `Risk Flag` and visible in status/priority metadata.
- Non-repetitive text: unique subjects and unique descriptions across generated backlog issues.
