"""Tests for the API health endpoint."""

from fastapi.testclient import TestClient

from sagent_agent_api.main import app

client = TestClient(app)


def test_health_returns_local_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "sagent-agent-api",
    }
