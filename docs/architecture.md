# Architecture

## Objective

Provide feature-level answers from Redmine issues/wiki with verifiable citations and low operational overhead on a MacBook Air M1 (16 GB).

## System components

- `API` (`FastAPI`): query, sync trigger, extraction trigger.
- `Storage` (`SQLite + FTS5`): raw payloads, normalized entities, chunk store.
- `Vector layer` (`LocalNumpyVectorStore`): pluggable local similarity index.
- `Ingestion` (`RedmineClient` + sync pipeline): incremental fetch and normalization.
- `Extraction`: deterministic metrics and later LLM JSON extraction.

## Data flow

1. `POST /v1/sync/redmine` queues a sync job.
2. Sync pipeline pulls changed Redmine entities from last watermark.
3. Texts are chunked and persisted to `doc_chunk`.
4. FTS triggers update lexical index automatically.
5. Vector index updates out-of-band through indexing jobs.
6. `POST /v1/ask` retrieves chunks and returns grounded response + citations.

## Non-functional priorities

- Deterministic ingestion.
- Citation traceability for each claim.
- Incremental updates with overlap window.
- Portable local development without external infra.
