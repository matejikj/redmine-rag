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
4. Generate eval results:
  - offline results: `python3 scripts/eval/run_eval.py --results <path-to-results.jsonl>`
  - live API run: `python3 scripts/eval/run_eval.py --api-base-url http://127.0.0.1:8000 --output-results evals/results.latest.jsonl`
5. Build and version baseline artifacts (when intentionally updating baseline):
  - `make eval-baseline`
  - commits `evals/results.baseline.v1.jsonl` and `evals/baseline_metrics.v1.json`
6. Run regression gate:
  - `make eval-gate`
  - compares current report against baseline with allowed metric drops
7. CI runs the same gate and fails on regression.

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

## Regression Gate

`scripts/eval/check_regression_gate.py` compares:

- current metrics report (`evals/reports/latest_eval_report.json`)
- baseline metrics (`evals/baseline_metrics.v1.json`)

Default allowed drops:

- citation coverage: `0.01`
- groundedness: `0.01`
- retrieval hit rate: `0.02`

If current performance drops below allowed bounds, the script exits non-zero and prints per-metric diagnostics.

## Adding New Eval Queries Safely

1. Add rows to `evals/supporthub_golden_v1.jsonl` with unique `id`.
2. Keep evidence targets explicit in `expected_sources` (with `source_type` + `source_id`).
3. Run `make eval` to verify dataset schema/coverage.
4. Regenerate baseline only when quality change is intentional:
  - `make eval-baseline`
  - review metric shifts
  - update `evals/CHANGELOG.md` with reason and impact.
