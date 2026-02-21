from fastapi.testclient import TestClient

from redmine_rag import main as main_module


def test_ui_index_returns_actionable_message_when_bundle_missing(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(main_module, "_FRONTEND_DIST_DIR", tmp_path / "missing-dist")
    client = TestClient(main_module.app)

    response = client.get("/app")

    assert response.status_code == 503
    payload = response.json()
    assert "Frontend build missing" in payload["detail"]


def test_ui_spa_route_returns_actionable_message_when_bundle_missing(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(main_module, "_FRONTEND_DIST_DIR", tmp_path / "missing-dist")
    client = TestClient(main_module.app)

    response = client.get("/app/sync")

    assert response.status_code == 503
    payload = response.json()
    assert "Frontend build missing" in payload["detail"]
