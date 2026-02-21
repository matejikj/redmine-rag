# Task 03: Chunking and Lexical Search (FTS5)

## Goal

Create chunk pipeline and high-quality lexical retrieval with SQLite FTS5.

## Scope

- Chunk textual content across all enabled Redmine entities:
  - issue descriptions, journals/comments, wiki content
  - attachments extracted text
  - news, documents, board messages (if enabled)
- Store chunk provenance (`source_type`, `source_id`, `url`, timestamps).
- Populate and maintain FTS index.

## Deliverables

- Chunk builder with stable chunk IDs.
- Re-index command for full rebuild.
- Lexical retrieval service using FTS + filters.

## Acceptance Criteria

- Query returns relevant chunks from issue/journal/wiki.
- Full re-index and incremental updates both work.
- Every chunk can be traced to a clickable source URL.

## Quality Gates

- Tests for chunk boundaries and overlap behavior.
- Retrieval tests with known expected hits.
- Performance check on local dataset.
