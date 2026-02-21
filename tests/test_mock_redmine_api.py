from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

import redmine_rag.mock_redmine.app as mock_redmine_app
from redmine_rag.mock_redmine.app import app

client = TestClient(app)
AUTH_HEADERS = {"X-Redmine-API-Key": "mock-api-key"}
ADMIN_HEADERS = {"X-Redmine-API-Key": "mock-api-key", "X-Mock-Role": "admin"}


def _fetch_all_issues(include: str | None = None) -> list[dict]:
    items: list[dict] = []
    offset = 0

    while True:
        params = {"limit": 100, "offset": offset}
        if include:
            params["include"] = include
        response = client.get("/issues.json", params=params, headers=ADMIN_HEADERS)
        assert response.status_code == 200
        payload = response.json()
        items.extend(payload["issues"])
        offset += payload["limit"]
        if offset >= payload["total_count"]:
            break

    return items


def _fetch_all_time_entries() -> list[dict]:
    items: list[dict] = []
    offset = 0

    while True:
        response = client.get(
            "/time_entries.json",
            params={"limit": 100, "offset": offset},
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200
        payload = response.json()
        items.extend(payload["time_entries"])
        offset += payload["limit"]
        if offset >= payload["total_count"]:
            break

    return items


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


def test_dataset_scale_and_balance() -> None:
    issues = client.get("/issues.json", headers=ADMIN_HEADERS).json()
    time_entries = client.get("/time_entries.json", headers=ADMIN_HEADERS).json()
    news = client.get("/news.json", headers=ADMIN_HEADERS).json()
    documents = client.get("/documents.json", headers=ADMIN_HEADERS).json()
    files = client.get("/files.json", headers=ADMIN_HEADERS).json()
    topics = client.get("/boards/94003/topics.json", headers=ADMIN_HEADERS).json()

    assert issues["total_count"] >= 200
    assert time_entries["total_count"] >= 300
    assert news["total_count"] >= 10
    assert documents["total_count"] >= 10
    assert files["total_count"] >= 10
    assert topics["total_count"] >= 10


def test_user_directory_has_realistic_role_coverage() -> None:
    response = client.get("/users.json", params={"limit": 100}, headers=AUTH_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert 15 <= payload["total_count"] <= 30

    roles = {user.get("role") for user in payload["users"] if user.get("role")}
    assert "Support Agent" in roles
    assert "Tech Lead" in roles
    assert "Product Owner" in roles
    assert "Customer Success" in roles
    assert "Security Engineer" in roles
    assert len(roles) >= 8


def test_role_based_assignment_and_handoff_trace() -> None:
    private_issue = client.get(
        "/issues/1000.json",
        params={"include": "journals"},
        headers=ADMIN_HEADERS,
    )
    normal_issue = client.get(
        "/issues/1001.json",
        params={"include": "journals"},
        headers=ADMIN_HEADERS,
    )

    assert private_issue.status_code == 200
    assert normal_issue.status_code == 200

    private_payload = private_issue.json()["issue"]
    normal_payload = normal_issue.json()["issue"]

    assert private_payload["assigned_to"]["id"] in {6, 18}
    assert normal_payload["assigned_to"]["id"] in {2, 10, 15}

    journal_user_ids = {
        item["user"]["id"] for item in normal_payload["journals"] if item.get("user")
    }
    assert len(journal_user_ids) >= 2


def test_issue_backlog_status_dependency_and_class_mix() -> None:
    issues = _fetch_all_issues(include="relations")

    assert len(issues) >= 120

    status_names = {issue["status"]["name"] for issue in issues}
    assert {"New", "In Progress", "Resolved", "Closed", "Reopened"} <= status_names

    relation_types = {
        relation["relation_type"] for issue in issues for relation in issue.get("relations", [])
    }
    assert {"blocks", "relates", "duplicates"} <= relation_types

    issue_classes = {
        field["value"]
        for issue in issues
        for field in issue["custom_fields"]
        if field["name"] == "Issue Class"
    }
    assert {"Epic", "Feature", "Bug", "Support", "Incident"} <= issue_classes


def test_issue_backlog_edge_cases_and_content_diversity() -> None:
    issues = _fetch_all_issues()
    bulk_issues = [issue for issue in issues if issue["id"] >= 1000]

    risk_flags = [
        field["value"]
        for issue in bulk_issues
        for field in issue["custom_fields"]
        if field["name"] == "Risk Flag"
    ]
    assert "Reopened" in risk_flags
    assert "Stalled" in risk_flags
    assert "Mis-prioritized" in risk_flags

    reopened_issues = [issue for issue in bulk_issues if issue["status"]["name"] == "Reopened"]
    assert len(reopened_issues) >= 5

    subjects = [issue["subject"] for issue in bulk_issues]
    descriptions = [issue["description"] for issue in bulk_issues]
    assert len(set(subjects)) == len(subjects)
    assert len(set(descriptions)) == len(descriptions)


def test_journal_comment_style_mix_and_non_generic_content() -> None:
    issues = _fetch_all_issues(include="journals")
    bulk_issues = [issue for issue in issues if issue["id"] >= 1000]
    notes = [
        journal["notes"]
        for issue in bulk_issues
        for journal in issue.get("journals", [])
        if journal.get("notes")
    ]
    private_note_values = [
        journal["private_notes"] for issue in bulk_issues for journal in issue.get("journals", [])
    ]

    assert any(note.startswith("Operational update:") for note in notes)
    assert any(note.startswith("Technical analysis:") for note in notes)
    assert any(note.startswith("Decision log:") for note in notes)
    assert any(note.startswith("Postmortem summary:") for note in notes)
    assert any("Root cause hypothesis:" in note for note in notes)

    assert any(private_note_values)
    assert any(not value for value in private_note_values)

    banned_generic_notes = {"done", "fixed", "ok", "resolved"}
    for note in notes:
        assert note.strip().lower() not in banned_generic_notes
        assert len(note.split()) >= 10


def test_journal_audit_trail_consistency_with_issue_state() -> None:
    issues = _fetch_all_issues(include="journals")
    bulk_issues = [issue for issue in issues if issue["id"] >= 1000]

    detail_names = {
        detail["name"]
        for issue in bulk_issues
        for journal in issue.get("journals", [])
        for detail in journal.get("details", [])
    }
    assert {"status_id", "assigned_to_id", "priority_id", "done_ratio"} <= detail_names

    issues_with_status_transition = 0
    for issue in bulk_issues:
        if issue["status"]["id"] == 1:
            continue
        status_details = [
            detail
            for journal in issue.get("journals", [])
            for detail in journal.get("details", [])
            if detail.get("name") == "status_id"
        ]
        assert status_details
        assert status_details[-1]["new_value"] == str(issue["status"]["id"])
        issues_with_status_transition += 1

    assert issues_with_status_transition >= 120


def test_time_entries_include_sla_and_outlier_patterns() -> None:
    time_entries = _fetch_all_time_entries()

    assert len(time_entries) >= 300

    comments = [entry["comments"] for entry in time_entries]
    assert any("SLA breach simulation" in comment for comment in comments)
    assert any("night shift incident response" in comment for comment in comments)
    assert any("escalation spike war-room" in comment for comment in comments)

    night_entries = [
        entry
        for entry in time_entries
        if ((hour := int(entry["created_on"][11:13])) < 6 or hour >= 22)
    ]
    assert len(night_entries) >= 8

    outlier_entries = [entry for entry in time_entries if entry["hours"] >= 5.0]
    assert len(outlier_entries) >= 10


def test_time_effort_distribution_is_plausible_by_class_and_status() -> None:
    issues = _fetch_all_issues()
    time_entries = _fetch_all_time_entries()

    issue_by_id = {issue["id"]: issue for issue in issues}
    hours_by_issue: dict[int, float] = {}
    for entry in time_entries:
        issue_ref = entry.get("issue")
        if issue_ref is None:
            continue
        issue_id = issue_ref["id"]
        hours_by_issue[issue_id] = hours_by_issue.get(issue_id, 0.0) + float(entry["hours"])

    incident_hours: list[float] = []
    support_hours: list[float] = []
    closed_hours: list[float] = []
    new_hours: list[float] = []

    for issue_id, issue in issue_by_id.items():
        if issue_id < 1000:
            continue
        total_hours = hours_by_issue.get(issue_id, 0.0)
        issue_class = next(
            (field["value"] for field in issue["custom_fields"] if field["name"] == "Issue Class"),
            "Support",
        )
        status_name = issue["status"]["name"]

        if issue_class == "Incident":
            incident_hours.append(total_hours)
        if issue_class == "Support":
            support_hours.append(total_hours)
        if status_name in {"Resolved", "Closed", "Reopened"}:
            closed_hours.append(total_hours)
        if status_name == "New":
            new_hours.append(total_hours)

    assert incident_hours
    assert support_hours
    assert closed_hours
    assert new_hours
    assert (sum(incident_hours) / len(incident_hours)) > (sum(support_hours) / len(support_hours))
    assert (sum(closed_hours) / len(closed_hours)) > (sum(new_hours) / len(new_hours))


def test_knowledge_layer_is_linked_to_issue_topics() -> None:
    news_payload = client.get("/news.json", params={"limit": 100}, headers=ADMIN_HEADERS).json()
    documents_payload = client.get(
        "/documents.json", params={"limit": 100}, headers=ADMIN_HEADERS
    ).json()
    files_payload = client.get("/files.json", params={"limit": 100}, headers=ADMIN_HEADERS).json()

    news = news_payload["news"]
    documents = documents_payload["documents"]
    files = files_payload["files"]

    assert news_payload["total_count"] >= 17
    assert documents_payload["total_count"] >= 20
    assert files_payload["total_count"] >= 25

    news_text = " ".join(
        f"{item['title']} {item['summary']} {item['description']}".lower() for item in news
    )
    assert "release update" in news_text
    assert "incident review" in news_text
    assert "process change" in news_text

    issue_reference_mentions = sum(
        "issue #" in item["description"].lower() for item in [*news, *documents, *files]
    )
    assert issue_reference_mentions >= 45

    file_names = [item["filename"].lower() for item in files]
    assert any("diagnostic-log" in name for name in file_names)
    assert any("rollback-checklist" in name for name in file_names)
    assert any("evidence-export" in name for name in file_names)


def test_wiki_revisions_are_citable_and_cross_referenced() -> None:
    titles = [
        "SLA-Metrics-Guide-1",
        "Evidence-Timeline-FAQ-2",
        "Root-Cause-Catalog-3",
        "Citation-Quality-Checklist-5",
    ]
    pages = []
    for title in titles:
        response = client.get(f"/projects/platform-core/wiki/{title}.json", headers=AUTH_HEADERS)
        assert response.status_code == 200
        pages.append(response.json()["wiki_page"])

    assert all(page["version"] >= 2 for page in pages)
    assert all("issue #" in page["text"].lower() for page in pages)
    assert all(page["comments"].lower().startswith("revision") for page in pages)
    assert any(page["parent"] is not None for page in pages)


def test_noisy_issue_profiles_are_present_but_controlled() -> None:
    issues = _fetch_all_issues(include="journals")
    bulk_issues = [issue for issue in issues if issue["id"] >= 1000]

    data_quality_flags = [
        next(
            (
                field["value"]
                for field in issue["custom_fields"]
                if field["name"] == "Data Quality Flag"
            ),
            "Clean",
        )
        for issue in bulk_issues
    ]
    noisy_count = sum(flag != "Clean" for flag in data_quality_flags)
    assert noisy_count >= 30
    assert noisy_count <= 120

    missing_workflow_stage = sum(
        not any(field["name"] == "Workflow Stage" for field in issue["custom_fields"])
        for issue in bulk_issues
    )
    assert 3 <= missing_workflow_stage <= 20

    incomplete_descriptions = sum(
        "todo: doplnit rca" in issue["description"].lower() for issue in bulk_issues
    )
    assert incomplete_descriptions >= 5

    inconsistent_priority = sum(
        "Inconsistent Priority Signal" in flag for flag in data_quality_flags
    )
    assert inconsistent_priority >= 3

    assert all(
        any(field["name"] == "Issue Class" for field in issue["custom_fields"])
        for issue in bulk_issues
    )


def test_noisy_language_and_legacy_artifacts_across_entities() -> None:
    issues = _fetch_all_issues(include="journals")
    bulk_issues = [issue for issue in issues if issue["id"] >= 1000]
    issue_text = " ".join(
        [issue["description"] for issue in bulk_issues]
        + [journal["notes"] for issue in bulk_issues for journal in issue.get("journals", [])]
    ).lower()

    assert "zákazník" in issue_text or "chybí" in issue_text
    assert "pls" in issue_text or "fyi" in issue_text
    assert "legacy note" in issue_text or "deprecated" in issue_text

    news = client.get("/news.json", params={"limit": 100}, headers=ADMIN_HEADERS).json()["news"]
    documents = client.get("/documents.json", params={"limit": 100}, headers=ADMIN_HEADERS).json()[
        "documents"
    ]
    files = client.get("/files.json", params={"limit": 100}, headers=ADMIN_HEADERS).json()["files"]

    topics = client.get(
        "/boards/94003/topics.json", params={"limit": 20}, headers=AUTH_HEADERS
    ).json()["messages"]
    thread_samples = topics[:6]
    thread_messages = [
        client.get(f"/messages/{topic['id']}.json", headers=AUTH_HEADERS).json()["message"]
        for topic in thread_samples
    ]

    combined_knowledge_text = " ".join(
        [item["description"] for item in news]
        + [item["description"] for item in documents]
        + [item["description"] for item in files]
        + [item["content"] for item in thread_messages]
        + [reply["content"] for item in thread_messages for reply in item["replies"]]
    ).lower()

    assert "deprecated" in combined_knowledge_text or "legacy" in combined_knowledge_text
    assert "issue #" in combined_knowledge_text
    assert "document #" in combined_knowledge_text


def test_requires_api_key() -> None:
    response = client.get("/issues.json")

    assert response.status_code == 401


def test_projects_hide_private_for_non_admin() -> None:
    response = client.get("/projects.json", headers=AUTH_HEADERS)

    assert response.status_code == 200
    projects = response.json()["projects"]
    assert len(projects) == 1
    assert projects[0]["identifier"] == "platform-core"


def test_projects_show_private_for_admin() -> None:
    response = client.get("/projects.json", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    projects = response.json()["projects"]
    assert len(projects) == 1
    assert projects[0]["identifier"] == "platform-core"


def test_issues_pagination_and_project_filter() -> None:
    response = client.get(
        "/issues.json",
        params={"project_id": "1", "limit": 1, "offset": 1},
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_count"] >= 100
    assert payload["offset"] == 1
    assert payload["limit"] == 1
    assert len(payload["issues"]) == 1


def test_issues_pagination_serializes_only_current_page(monkeypatch: pytest.MonkeyPatch) -> None:
    serialized_issue_ids: list[int] = []
    serialize_issue = mock_redmine_app._serialize_issue

    def _tracked_serialize_issue(issue: dict[str, Any], include_fields: set[str]) -> dict[str, Any]:
        serialized_issue_ids.append(int(issue["id"]))
        return serialize_issue(issue, include_fields=include_fields)

    monkeypatch.setattr(mock_redmine_app, "_serialize_issue", _tracked_serialize_issue)

    response = client.get(
        "/issues.json",
        params={"project_id": "1", "limit": 2, "offset": 3},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["issues"]) == 2
    assert serialized_issue_ids == [issue["id"] for issue in payload["issues"]]
    assert len(serialized_issue_ids) == 2


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


def test_communication_threads_have_links_and_decision_points() -> None:
    arch_topics_response = client.get("/boards/94001/topics.json", headers=AUTH_HEADERS)
    ops_topics_response = client.get("/boards/94003/topics.json", headers=AUTH_HEADERS)

    assert arch_topics_response.status_code == 200
    assert ops_topics_response.status_code == 200

    arch_topics = arch_topics_response.json()["messages"]
    ops_topics = ops_topics_response.json()["messages"]

    assert len(ops_topics) >= 10
    assert any("architecture review" in topic["subject"].lower() for topic in ops_topics)
    assert any("ops review" in topic["subject"].lower() for topic in ops_topics)

    topic_ids = [topic["id"] for topic in arch_topics[:2]] + [
        topic["id"] for topic in ops_topics[:6]
    ]
    details = [
        client.get(f"/messages/{message_id}.json", headers=AUTH_HEADERS).json()["message"]
        for message_id in topic_ids
    ]

    combined_content = " ".join(
        [message["content"] for message in details]
        + [reply["content"] for message in details for reply in message["replies"]]
    ).lower()

    assert "issue #" in combined_content
    assert "document #" in combined_content
    assert "decision point" in combined_content or "decision:" in combined_content
    assert any(
        len(message["replies"]) >= 1 for message in details if message["board"]["id"] == 94003
    )


def test_private_security_board_content_for_admin() -> None:
    topics_response = client.get("/boards/94002/topics.json", headers=ADMIN_HEADERS)
    message_response = client.get("/messages/95999.json", headers=ADMIN_HEADERS)

    assert topics_response.status_code == 200
    assert message_response.status_code == 200

    topics = topics_response.json()["messages"]
    message = message_response.json()["message"]

    assert len(topics) == 1
    assert topics[0]["id"] == 95999
    assert "issue #301" in message["content"].lower()
    assert "decision:" in message["content"].lower()
    assert message["locked"] is True


def test_private_board_is_forbidden_without_admin() -> None:
    response = client.get("/boards/94002/topics.json", headers=AUTH_HEADERS)

    assert response.status_code == 403
