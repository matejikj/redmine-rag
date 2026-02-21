from fastapi.testclient import TestClient

from redmine_rag.main import app


def test_ui_index_returns_actionable_message_when_bundle_missing() -> None:
    client = TestClient(app)

    response = client.get("/app")

    assert response.status_code == 503
    payload = response.json()
    assert "Frontend build missing" in payload["detail"]


def test_ui_spa_route_returns_actionable_message_when_bundle_missing() -> None:
    client = TestClient(app)

    response = client.get("/app/sync")

    assert response.status_code == 503
    payload = response.json()
    assert "Frontend build missing" in payload["detail"]
