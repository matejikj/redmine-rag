from fastapi.testclient import TestClient

from redmine_rag.main import app


def test_ask_returns_grounded_fallback_when_no_data() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/ask",
        json={
            "query": "Jaké vlastnosti má feature jednotné přihlášení?",
            "filters": {"project_ids": []},
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"] == []
    assert payload["used_chunk_ids"] == []
    assert payload["confidence"] == 0.0
