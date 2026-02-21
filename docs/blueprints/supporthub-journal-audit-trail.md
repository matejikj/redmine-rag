# SupportHub Journal & Audit Trail Blueprint (Data Task 4)

## Goal
Model issue journals as realistic multi-role conversations with a reliable audit trail for workflow decisions.

## Journal Conversation Model
Each issue journal thread should include multiple styles:
- `Operational update`: intake, customer impact, ownership acknowledgement.
- `Technical analysis`: root-cause hypothesis and investigation evidence.
- `Decision log`: explicit remediation/ownership/prioritization decision.
- `Postmortem summary`: closure rationale and prevention follow-up.

## Audit Details Model
Journal `details` must include structured changes for:
- `status_id`
- `assigned_to_id`
- `priority_id`
- `done_ratio`

Rules:
- For non-`New` issues, status transitions must exist and final transition must match issue final status.
- `done_ratio` progression should be monotonic and end at issue-level `done_ratio`.
- Reassignments and priority changes must be represented by attribute transitions.

## Privacy and Access Behavior
- Public and private notes are mixed in dataset.
- Private issues contain private journals.
- Incident/security decision notes may be private even in otherwise non-private workflows.

## Realism Constraints
- Notes include account, channel, region, root-cause, and action context.
- No generic low-information notes such as `done`, `fixed`, `ok`.
- Journal content supports reconstruction of:
  - root-cause trajectory
  - ownership handoff
  - decision rationale

## Acceptance Mapping
- Style diversity: covered by operational/technical/decision/postmortem note types.
- Structured audit trail: covered by required `details` fields and transition rules.
- Reconstructability: covered by explicit root-cause + decision narrative.
- Non-generic comments: enforced by template design and tests.
