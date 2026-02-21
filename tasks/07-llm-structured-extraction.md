# Task 07: LLM Structured Extraction (JSON Schema)

## Goal

Add controlled LLM extraction for higher-level properties.

## Scope

- Define strict JSON schema for extracted properties.
- Implement batch extraction over selected issues.
- Version prompts and extractor outputs.

## Deliverables

- Extraction pipeline with retries and error buckets.
- Schema validation layer before persistence.
- `extractor_version` strategy and migration-safe output model.

## Acceptance Criteria

- Invalid JSON responses are rejected and retried safely.
- Stored properties include confidence and version metadata.
- Extraction can be re-run deterministically per version.

## Quality Gates

- Tests for schema validation and bad-output handling.
- Prompt files versioned in repo.
- Cost/latency limits documented.
