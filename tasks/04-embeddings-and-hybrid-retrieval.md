# Task 04: Embeddings and Hybrid Retrieval

## Goal

Add semantic retrieval and merge it with lexical search.

## Scope

- Compute embeddings for chunks (batch pipeline).
- Store vectors in local backend.
- Combine lexical + vector candidates with rank fusion.

## Deliverables

- Embedding job with incremental updates.
- Hybrid retriever interface with scoring diagnostics.
- Configurable `top_k`, weights, and filter behavior.

## Acceptance Criteria

- Hybrid retrieval outperforms lexical-only on eval set.
- Vector store survives restart and supports reindex.
- Retrieval debug output explains why chunks were selected.

## Quality Gates

- Tests for fusion logic and fallback behavior.
- Reproducible retrieval results across runs.
- Profiling notes for M1/16GB constraints.
