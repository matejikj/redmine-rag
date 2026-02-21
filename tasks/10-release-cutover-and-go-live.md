# Task 10: Release Cutover and Go-Live

## Goal

Execute production cutover from mock API to real Redmine with minimal risk.

## Scope

- Final UAT with real data subset.
- Switch API URL and credentials via environment config.
- Validate end-to-end behavior and quality metrics.

## Deliverables

- Go-live checklist and rollback plan.
- Production environment variables and secret configuration guide.
- Post-launch monitoring checklist (first 7 days).

## Acceptance Criteria

- URL switch requires config change only.
- Sync, retrieval, ask, and citations work on production Redmine across all enabled modules.
- Quality metrics stay within accepted thresholds after go-live.

## Quality Gates

- Release candidate tagged and validated.
- Signed-off UAT report.
- Post-go-live review completed.
