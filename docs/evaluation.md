# Evaluation

## Why

RAG quality must be measured continuously, not guessed.

## Minimum metrics

- Citation coverage: share of claims with at least one source.
- Groundedness: share of claims supported by retrieved chunks.
- Retrieval hit rate: proportion of questions where relevant chunk appears in top K.
- Source-type coverage: distribution of used evidence across Redmine source types (issues, journals, wiki, time entries, news, documents, messages, ...).

## Loop

1. Maintain the golden JSONL dataset in `evals/supporthub_golden_v1.jsonl`.
2. Rebuild dataset deterministically with `python3 scripts/eval/build_supporthub_golden.py` when needed.
3. Run `make eval` (dataset validation + coverage report).
4. Run `python3 scripts/eval/run_eval.py --results <path-to-results.jsonl>` to compute metrics.
5. Track changes in quality when retrieval/prompt/model changes.
6. Block regressions in CI once thresholds are finalized.

## Results JSONL Contract

Each result row must contain:

- `id` (string, matches golden query id)
- `claims_total` (int)
- `claims_with_citation` (int)
- `claims_grounded` (int)
- `retrieved_sources` (list of source refs with `source_type` + `source_id`)
- `cited_sources` (list of source refs with `source_type` + `source_id`)

This enables automatic computation of:

- citation coverage
- groundedness
- retrieval hit rate (expected vs retrieved evidence overlap)
- cited source-type coverage
