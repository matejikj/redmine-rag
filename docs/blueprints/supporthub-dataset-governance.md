# SupportHub Dataset Governance Blueprint (Data Task 10)

## Goal
Finalize a production-ready mock dataset with stable versioning, profile variants, and enforceable quality gates.

## Stable Versioning
- Stable dataset release: `supporthub_mock_dataset_v1`.
- Manifest file: `evals/mock_dataset_manifest.v1.json`.
- Changelog: `evals/CHANGELOG.md`.

Governance rule:
- Any dataset change must update either manifest metadata (if contract changes) or changelog (if content/quality changes).

## Profile Variants (Same Semantics)
Profiles are selected by `MOCK_REDMINE_DATASET_PROFILE`:
- `small`
- `medium`
- `large` (default)

Profiles differ only in scale (counts), not in semantic model:
- same issue classes
- same status model
- same relation types
- same noisy-data categories
- same security/private visibility rules

## Quality Gates
Automated checker:
- Script: `scripts/eval/check_mock_dataset_quality.py`
- Modes:
  - single profile check
  - all profiles check (`--all-profiles`)

Validated dimensions:
- schema-level consistency (required fields and IDs)
- linkage integrity (relations, time entries, message authors/boards)
- scenario coverage (classes, statuses, relation types, risk flags)
- noisy-data coverage and bounds
- private/security data consistency

## CI Integration
Dataset quality checks are part of the standard quality pipeline:
- `scripts/check.sh` runs quality checker for all profiles.
- CI workflow runs `./scripts/check.sh`, therefore dataset regressions fail CI.

## Acceptance Mapping
- Stable v1 + changelog: provided by manifest + changelog artifacts.
- Profile variants with same semantics: enforced by profile config + checker.
- CI data quality checks: enforced by `check.sh` integration.
