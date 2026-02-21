from fastapi.testclient import TestClient

from redmine_rag.main import app


def test_sync_request_rejects_negative_project_ids() -> None:
    client = TestClient(app)
    response = client.post("/v1/sync/redmine", json={"project_ids": [1, -2]})
    assert response.status_code == 422


def test_sync_request_rejects_unknown_modules() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/sync/redmine",
        json={"project_ids": [1], "modules": ["issues", "unknown"]},
    )
    assert response.status_code == 422


def test_extract_request_rejects_negative_issue_ids() -> None:
    client = TestClient(app)
    response = client.post("/v1/extract/properties", json={"issue_ids": [10, -1]})
    assert response.status_code == 422


def test_sync_jobs_filter_rejects_unknown_status() -> None:
    client = TestClient(app)
    response = client.get("/v1/sync/jobs", params={"status": "broken"})
    assert response.status_code == 422
