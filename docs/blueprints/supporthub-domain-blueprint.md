# SupportHub Domain Blueprint (Data Task 1)

## 1. Project Scope

Project identity:
- `identifier`: `platform-core`
- `name`: `SupportHub Platform`

Business objective:
- Improve support operations by reducing response time, improving resolution quality, and making incident decisions traceable through evidence and citations.

Primary business outcomes:
- Lower SLA breaches.
- Faster and more accurate triage.
- Reproducible post-incident analysis.
- Better knowledge reuse from wiki/documents.

## 2. Roles and Responsibilities

Core roles:
- `Support Agent`: handles intake, triage, follow-up with customer.
- `Tech Lead`: owns root-cause and technical decision-making.
- `Product Owner`: prioritization, scope tradeoffs, roadmap alignment.
- `Customer Success`: customer impact and communication quality.
- `Security Engineer`: sensitive incidents and compliance constraints.

Responsibility boundaries:
- Agent owns status updates and first response evidence.
- Tech Lead owns root-cause notes and remediation proof.
- Product Owner owns priority overrides and acceptance criteria.
- Security Engineer owns private records and risk classification.

## 3. Workstreams

`Authentication`:
- Login reliability, session integrity, role mapping.

`SLA Automation`:
- Response timers, escalation rules, breach prevention.

`Evidence Timeline`:
- Unified event history from issues, journals, and time entries.

`Knowledge Base`:
- Article quality, freshness, and linkage to recurring incidents.

`Reporting & Citations`:
- Grounded summaries and source traceability.

## 4. Ticket Taxonomy

Trackers:
- `Bug`: defect in behavior or reliability.
- `Feature`: planned capability increment.
- `Support`: operational request or customer-driven case.

Issue classes (semantic tags via custom fields):
- `Incident`, `Problem`, `Change`, `Request`.

Priority model:
- `Low`, `Normal`, `High`, `Urgent`.

Required custom fields for data realism:
- `Module`
- `Workstream`
- `Customer Segment`
- `Customer Impact`
- `Workflow Stage`

## 5. Lifecycle and State Logic

State set:
- `New` -> `In Progress` -> `Resolved` -> `Closed`

Allowed exceptions:
- `Resolved` -> `In Progress` (reopen with cause in journal)
- `Closed` -> `In Progress` (critical regression only, private note required)

Behavioral requirements:
- Every state transition must have a journal event.
- Reopen must include explicit reason (`details` + `notes`).
- Assignee change without comment is invalid in curated dataset.

## 6. SLA Rules

Response SLA (first non-empty agent/lead journal):
- `Urgent`: 15 minutes
- `High`: 1 hour
- `Normal`: 4 hours
- `Low`: 1 business day

Resolution SLA (from `created_on` to terminal state):
- `Urgent`: 8 hours
- `High`: 24 hours
- `Normal`: 5 days
- `Low`: 10 days

Escalation policy:
- 80% SLA threshold triggers warning event.
- Breach triggers escalation note + owner change evidence.

## 7. Entity Relationship Map

Operational core:
- `issue` 1:N `journal`
- `issue` 1:N `time_entry`
- `issue` 1:N `attachment`
- `issue` N:M `user_entity` via watchers
- `issue` N:M `issue` via relations

Knowledge and communication:
- `wiki_page` 1:N `wiki_version`
- `board` 1:N `message`
- `message` 1:N replies
- `news` and `document` reference the same project timeline

Retrieval and explainability:
- Any textual entity -> `doc_chunk`
- `doc_chunk` must keep source URL and source identifiers

## 8. Realistic Scenario Families

Data must include these families with unique narratives:
- `SLA drift`: repeated near-breach tickets by module.
- `Escalation loop`: handoff churn before stable owner.
- `Knowledge gap`: recurring issue where wiki was stale.
- `Evidence mismatch`: summary claims not aligned with source.
- `Security incident`: private notes and restricted board trail.
- `False closure`: issue closed too early and reopened.

## 9. Cross-Entity Consistency Rules

Hard consistency rules:
- All entities belong to `project_id=1` for this dataset profile.
- `issue.updated_on` >= max(`journal.created_on`, `time_entry.updated_on`).
- `closed_on` is set only when status is terminal (`Resolved`/`Closed` in dataset semantics).
- Any private issue must have at least one private journal entry.
- Any relation points to an existing issue ID.
- Any attachment linked to an issue/journal must reference existing parent.

Soft realism rules:
- At least 20% issues include attachments or technical evidence.
- At least 15% issues are reopened at least once.
- At least 30% issues reference wiki/doc/document context in journals.
- At least 10% issues include cross-team handoff.

## 10. Acceptance Mapping to Data Task 1

Acceptance criteria mapping:
- Clear business meaning per entity: covered in sections 2, 3, 7.
- Gap-free relationship description: covered in section 7.
- No generic placeholder scenarios: covered by section 8 scenario families and section 9 rules.
