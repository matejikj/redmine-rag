# Task 01: Mock Redmine API (Development Blocker Removal)

## Goal

Build a local Mock Redmine API with broad data coverage so development can continue without access to the real Redmine.

## Scope

- Implement a local HTTP service that mimics Redmine endpoints used by our system.
- Use deterministic fixture data for all key Redmine data domains, including comments/journals.
- Provide realistic `updated_on` behavior to test incremental sync.

## Deliverables

- `mock-redmine` service (FastAPI) with endpoints:
  - `GET /issues.json`
  - `GET /issues/{id}.json`
  - `GET /projects.json`
  - `GET /users.json`
  - `GET /groups.json`
  - `GET /trackers.json`
  - `GET /issue_statuses.json`
  - `GET /enumerations/issue_priorities.json`
  - `GET /time_entries.json`
  - `GET /news.json`
  - `GET /documents.json` and/or `GET /files.json` (depending on enabled modules)
  - `GET /boards/{id}/topics.json` and `GET /messages/{id}.json` (if enabled modules are simulated)
  - `GET /projects/{project}/wiki/{title}.json`
- Fixture set with multiple projects and mixed states for:
  - issues, journals/notes, attachments, relations, watchers, custom fields
  - wiki pages + versions
  - time entries
  - users/groups/memberships
- Run script + docs for starting mock service locally.
- Env toggle to switch between mock and real Redmine by URL only.

## Acceptance Criteria

- Existing sync flow runs end-to-end against mock service.
- Pagination and `updated_on` filters are covered by tests.
- `include=` expansions are supported where needed (`journals`, `attachments`, `relations`, `watchers`, `children`).
- The project can switch from mock to production via `.env` change only.

## Quality Gates

- Contract tests for all mocked endpoints.
- Deterministic fixtures committed to repository.
- Negative-path tests for missing entities, permission-like restrictions, and malformed params.
- No hardcoded production values in code.
