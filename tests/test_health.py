from fastapi.testclient import TestClient

from redmine_rag.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "redmine-rag"
