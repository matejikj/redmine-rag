# Mock Dataset Changelog

## v1.0.0 (2026-02-21)

Initial stable release of the SupportHub mock dataset governance baseline.

### Included capabilities
- Realistic cross-entity dataset for one project (`platform-core`) with issues, journals, time entries, wiki, news, documents, files, boards, and messages.
- Deterministic edge-case profiles: reopened/stalled/mis-prioritized tickets and controlled noisy data.
- Golden evaluation dataset (`supporthub_golden_v1.jsonl`) with expected evidence sources.
- Profile variants (`small`, `medium`, `large`) with the same semantics and different scale.
- Data quality checks script for schema/linkage/scenario coverage validation.

### Compatibility
- Default runtime profile: `large`.
- Profile selector: `MOCK_REDMINE_DATASET_PROFILE`.
- Backward compatible API routes with existing mock Redmine contract.

## v1.1.0 (2026-02-21)

Evaluation and regression gate artifacts added.

### Included capabilities
- Baseline eval results fixture: `evals/results.baseline.v1.jsonl`.
- Baseline metrics snapshot: `evals/baseline_metrics.v1.json`.
- Eval report output and regression gate workflow for CI/non-regression checks.
