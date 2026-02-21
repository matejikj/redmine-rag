# SupportHub Time & SLA Blueprint (Data Task 5)

## Goal
Provide realistic time-entry behavior that supports KPI analytics, SLA validation, and operational outlier detection.

## Time Entry Model
Time entries are generated per issue with deterministic logic tied to:
- issue class (`Epic`, `Feature`, `Bug`, `Support`, `Incident`)
- issue status (`New`, `In Progress`, `Resolved`, `Closed`, `Reopened`)
- risk flag (`None`, `Reopened`, `Stalled`, `Mis-prioritized`)

Each issue has:
- first-response entry (support/incident handling)
- follow-up execution entries (development, QA, escalation, coordination)

## SLA Response Pattern
Response targets by priority:
- `Low`: 24h
- `Normal`: 4h
- `High`: 1h
- `Urgent`: 15m

Dataset includes deterministic breach scenarios:
- comment marker: `SLA breach simulation`
- delayed first response beyond target threshold

## Resolution / Effort Distribution
Expected workload distribution:
- incidents are heavier than support tickets
- resolved/closed issues carry more effort than new issues
- stalled issues contain low-progress follow-up entries while waiting for external input

## Outliers
Required outlier patterns:
- `night shift incident response` entries (night timestamps)
- `escalation spike war-room` entries (high-hour bursts)

## Data Quality Rules
- Every time entry references existing issue + user.
- `spent_hours` on issue reflects aggregated recorded effort.
- Comments include operational context (account/scenario) and are not generic placeholders.

## Acceptance Mapping
- Time entries linked to issues/users: satisfied by deterministic mapping.
- Realistic distributions: satisfied by class/status-driven iteration and hour logic.
- Reproducible SLA breaches: satisfied by deterministic delay rules + comment marker.
- Outliers present: satisfied by night and escalation spike generators.
