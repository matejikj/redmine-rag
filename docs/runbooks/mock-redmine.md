# Mock Redmine Runbook

## Purpose

Run a local Redmine-compatible mock API for development before real Redmine access is available.

## Start service

```bash
make mock-redmine
```

Default endpoint: `http://127.0.0.1:8081`

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
- Private project access is allowed only with header `X-Mock-Role: admin`.
