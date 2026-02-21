# Architecture

## Objective

Provide feature-level answers from full Redmine data (not only issues/wiki) with verifiable citations and low operational overhead on a MacBook Air M1 (16 GB).

## System components

- `API` (`FastAPI`): query, sync trigger, extraction trigger.
- `Ops API` (`FastAPI`): health diagnostics and sync job introspection.
- `Storage` (`SQLite + FTS5`): generic raw payloads (`raw_entity`), normalized entities, chunk store.
- `Vector layer` (`LocalNumpyVectorStore`): pluggable local similarity index.
- `Ingestion` (`RedmineClient` + sync pipeline): incremental fetch and normalization.
- `Extraction`: deterministic metrics + controlled LLM JSON extraction with schema validation/retries.

## Redmine data coverage target

- Work items: issues, journals/comments, attachments, relations, watchers, custom fields.
- Knowledge: wiki pages + versions.
- Effort tracking: time entries.
- Delivery and planning: versions/releases, categories, trackers, statuses, priorities.
- Organization: projects, users, groups, memberships.
- Communication modules (when enabled): news, documents/files, boards/messages.

## Data model strategy

- Generic raw ingest for all endpoints: store untouched payloads in `raw_entity`.
- Compatibility raw tables for core domains: `raw_issue`, `raw_journal`, `raw_wiki`.
- Normalized tables for cross-entity querying: projects, users/groups, workflow enums, issues+journals, wiki+versions, time entries, attachments, communication modules, custom fields/values.
- Chunk-level provenance for all source types in `doc_chunk`.

## Data flow

1. `POST /v1/sync/redmine` queues a sync job.
2. Sync pipeline pulls changed Redmine entities from last watermark.
3. Texts are chunked and persisted to `doc_chunk`.
4. FTS triggers update lexical index automatically.
5. Vector index updates out-of-band through indexing jobs.
6. `POST /v1/ask` retrieves chunks and returns grounded response + citations.
7. `GET /v1/sync/jobs` and `GET /healthz` expose operational state for automation.

## Non-functional priorities

- Deterministic ingestion.
- Citation traceability for each claim.
- Incremental updates with overlap window.
- Portable local development without external infra.

## Hybrid Retrieval Profiling Notes (M1 / 16 GB)

- Default `EMBEDDING_DIM=256` keeps vector memory low while preserving useful semantic recall for local datasets.
- Candidate fanout is controlled via `RETRIEVAL_CANDIDATE_MULTIPLIER` (default `4`) to cap SQL + fusion overhead.
- Weighted RRF (`RETRIEVAL_RRF_K=60`) stabilizes ranking when lexical/vector scores are on different scales.
- Local vector store persists as `numpy` matrix + key metadata on disk; restart does not require recomputing vectors.
- Recommended local flow for predictable latency:
  1. run incremental sync (`make sync`)
  2. keep embeddings refreshed incrementally (automatic in sync; manual with `make embed` when needed)
  3. use full rebuild (`make reindex`) only after schema/content migrations
