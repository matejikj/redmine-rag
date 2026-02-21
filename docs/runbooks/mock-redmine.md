# Mock Redmine Runbook

## Purpose

Run a local Redmine-compatible mock API for development before real Redmine access is available.

## Start service

```bash
make mock-redmine
```

Default endpoint: `http://127.0.0.1:8081`

Optional dataset scale profile (default `large`):

```bash
MOCK_REDMINE_DATASET_PROFILE=small make mock-redmine
```

Available profiles:
- `small`
- `medium`
- `large`

## Configure app to use mock API

In `.env`:

```bash
REDMINE_BASE_URL=http://127.0.0.1:8081
REDMINE_API_KEY=mock-api-key
```

## Switch to production later

Replace only these values:

```bash
REDMINE_BASE_URL=https://your-real-redmine.example.com
REDMINE_API_KEY=<real-key>
```

No code changes are required for cutover.

## Supported mock endpoints

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
- `GET /documents.json`
- `GET /files.json`
- `GET /boards/{id}/topics.json`
- `GET /messages/{id}.json`
- `GET /projects/{project}/wiki/{title}.json`

## Notes

- Auth header is required: `X-Redmine-API-Key`.
- Default mock API key is `mock-api-key`.
- Private records (private issues and private boards) are visible only with `X-Mock-Role: admin`.
- Dataset is intentionally large (200+ issues) to simulate realistic sync and retrieval load.
- Endpoint handlers use page-first filtering/serialization and pre-indexed topic/wiki lookups to
  stay responsive with larger fixture volumes.
- Fixtures are coherent around one project theme (`platform-core` / SupportHub Platform).
- Dataset governance baseline and changelog are stored in `evals/mock_dataset_manifest.v1.json` and `evals/CHANGELOG.md`.
- Run profile quality checks with:

```bash
make dataset-quality
```
