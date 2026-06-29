"""Tests for the deterministic task placeholder."""

from fastapi.testclient import TestClient
from sagent_agent_api.main import app

client = TestClient(app)


def test_task_returns_structured_placeholder_response() -> None:
    response = client.post(
        "/agent/task",
        json={"task": "Erstelle einen sicheren Plan"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "message": (
            "Aufgabe „Erstelle einen sicheren Plan“ wurde lokal angenommen. "
            "Diese Minimalversion führt noch keine Änderungen aus."
        ),
        "next_steps": [
            "Anforderungen und Projektkontext prüfen",
            "Einen kontrollierten Arbeitsplan vorbereiten",
            "Vor jeder Änderung eine Freigabe einholen",
        ],
    }


def test_task_rejects_whitespace_only_input() -> None:
    response = client.post("/agent/task", json={"task": "   "})

    assert response.status_code == 422
