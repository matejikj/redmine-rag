from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from redmine_rag.mock_redmine.app import app

client = TestClient(app)
AUTH_HEADERS = {"X-Redmine-API-Key": "mock-api-key"}
ADMIN_HEADERS = {"X-Redmine-API-Key": "mock-api-key", "X-Mock-Role": "admin"}


@pytest.mark.parametrize(
    ("path", "payload_key"),
    [
        ("/projects.json", "projects"),
        ("/users.json", "users"),
        ("/groups.json", "groups"),
        ("/issues.json", "issues"),
        ("/time_entries.json", "time_entries"),
        ("/news.json", "news"),
        ("/documents.json", "documents"),
        ("/files.json", "files"),
    ],
)
def test_list_contracts(path: str, payload_key: str) -> None:
    response = client.get(path, headers=AUTH_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload_key in payload
    assert "total_count" in payload
    assert "offset" in payload
    assert "limit" in payload


def test_requires_api_key() -> None:
    response = client.get("/issues.json")

    assert response.status_code == 401


def test_projects_hide_private_for_non_admin() -> None:
    response = client.get("/projects.json", headers=AUTH_HEADERS)

    assert response.status_code == 200
    project_ids = {project["id"] for project in response.json()["projects"]}
    assert 3 not in project_ids


def test_projects_show_private_for_admin() -> None:
    response = client.get("/projects.json", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    project_ids = {project["id"] for project in response.json()["projects"]}
    assert 3 in project_ids


def test_issues_pagination_and_project_filter() -> None:
    response = client.get(
        "/issues.json",
        params={"project_id": "1", "limit": 1, "offset": 1},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_count"] == 3
    assert payload["offset"] == 1
    assert payload["limit"] == 1
    assert len(payload["issues"]) == 1


def test_issues_updated_on_filter() -> None:
    response = client.get(
        "/issues.json",
        params={"updated_on": ">=2026-02-19T00:00:00Z"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    issue_ids = {issue["id"] for issue in response.json()["issues"]}
    assert issue_ids == {102, 201}


def test_issue_include_expansions() -> None:
    response = client.get(
        "/issues/101.json",
        params={"include": "journals,attachments,relations,watchers,children"},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    issue = response.json()["issue"]
    assert "journals" in issue
    assert "attachments" in issue
    assert "relations" in issue
    assert "watchers" in issue
    assert "children" in issue
    assert issue["journals"][0]["notes"]


def test_private_issue_permission_like_restriction() -> None:
    forbidden = client.get("/issues/301.json", headers=AUTH_HEADERS)
    allowed = client.get("/issues/301.json", headers=ADMIN_HEADERS)

    assert forbidden.status_code == 403
    assert allowed.status_code == 200


def test_wiki_by_identifier_and_missing_page() -> None:
    ok_response = client.get(
        "/projects/platform-core/wiki/Feature-Login.json",
        headers=AUTH_HEADERS,
    )
    missing_response = client.get(
        "/projects/platform-core/wiki/does-not-exist.json",
        headers=AUTH_HEADERS,
    )

    assert ok_response.status_code == 200
    assert ok_response.json()["wiki_page"]["title"] == "Feature-Login"
    assert missing_response.status_code == 404


def test_malformed_params() -> None:
    invalid_limit = client.get(
        "/issues.json",
        params={"limit": -1},
        headers=AUTH_HEADERS,
    )
    invalid_project_filter = client.get(
        "/issues.json",
        params={"project_id": "abc"},
        headers=AUTH_HEADERS,
    )

    assert invalid_limit.status_code == 422
    assert invalid_project_filter.status_code == 422


def test_board_topics_and_message_details() -> None:
    topics_response = client.get("/boards/94001/topics.json", headers=AUTH_HEADERS)
    message_response = client.get("/messages/95001.json", headers=AUTH_HEADERS)

    assert topics_response.status_code == 200
    assert message_response.status_code == 200
    assert topics_response.json()["messages"][0]["id"] == 95001
    assert message_response.json()["message"]["id"] == 95001
    assert len(message_response.json()["message"]["replies"]) == 1


def test_private_board_is_forbidden_without_admin() -> None:
    response = client.get("/boards/94002/topics.json", headers=AUTH_HEADERS)

    assert response.status_code == 403
