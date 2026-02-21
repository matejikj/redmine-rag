# SupportHub Noisy Data Profile Blueprint (Data Task 8)

## Goal
Introduce controlled real-world data noise and inconsistencies so retrieval and citation logic can be stress-tested.

## Noise Categories
- Incomplete issue descriptions (`TODO` placeholders, missing context).
- Missing metadata field on subset of records (e.g., missing `Workflow Stage`).
- Priority inconsistency signals (legacy severity says critical while queue priority is low).
- Noisy comments with CZ/EN mix, abbreviations, and domain slang.
- Historical artifacts using deprecated terminology.

## Controlled Injection Strategy
Noise is deterministic (index-based), not random, to keep evaluation reproducible.

Per-issue controls:
- `Data Quality Flag` custom field summarizes active noise tags.
- `Clean` remains majority baseline.
- Noisy subset is bounded and traceable.

## Language and Terminology
Data deliberately contains mixed language and support slang:
- CZ tokens (e.g., `zákazník`, `chybí`, `doplnit`).
- EN shorthand (`FYI`, `pls`, `ASAP`).
- Legacy/deprecated terms retained for audit realism.

## Cross-Entity Noise
Noise is present not only in issues/journals but also in:
- wiki revisions
- news and documents
- file descriptions
- board message threads

## Acceptance Mapping
- RAG robustness: noisy and incomplete records are present in controlled volume.
- Citation resilience: noisy entities still include issue/document references.
- Documentation: noise schema and bounds are defined via `Data Quality Flag` and this profile.
