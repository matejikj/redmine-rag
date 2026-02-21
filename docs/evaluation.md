# Evaluation

## Why

RAG quality must be measured continuously, not guessed.

## Minimum metrics

- Citation coverage: share of claims with at least one source.
- Groundedness: share of claims supported by retrieved chunks.
- Retrieval hit rate: proportion of questions where relevant chunk appears in top K.

## Loop

1. Maintain a JSONL dataset in `evals/`.
2. Run `make eval` locally.
3. Track changes in quality when retrieval/prompt/model changes.
4. Block regressions in CI once evaluator is fully implemented.
