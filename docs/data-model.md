# Data Model

## Raw layer

- `raw_entity`: generic storage for any Redmine endpoint payload.
- Compatibility raw tables for core domains:
  - `raw_issue`
  - `raw_journal`
  - `raw_wiki`

## Reference entities

- `project`
- `user_entity`
- `group_entity`
- `membership`
- `tracker`
- `issue_status`
- `issue_priority`
- `issue_category`
- `version`
- `custom_field`
- `custom_value`

## Work and collaboration entities

- `issue`
- `journal` (comments/notes + details)
- `issue_relation`
- `issue_watcher`
- `wiki_page`
- `wiki_version`
- `time_entry`
- `attachment`
- `news`
- `document`
- `board`
- `message`

## Retrieval and analytics entities

- `doc_chunk` (all source types, full citation provenance)
- `issue_metric`
- `issue_property`

## Sync state entities

- `sync_cursor` (per entity-type cursor)
- `sync_state` (global state)
- `sync_job` (job lifecycle)
