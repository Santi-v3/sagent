"""Tests for the deterministic planning and approval workflow."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sagent_agent_api.main import app

client = TestClient(app)


def create_plan(task: str = "Erweitere die API und Web-UI") -> dict[str, object]:
    response = client.post("/agent/plan", json={"task": task})
    assert response.status_code == 201
    return response.json()


def test_plan_contains_goal_steps_risks_actions_and_proposal() -> None:
    plan = create_plan()

    assert plan["approval_state"] == "pending"
    assert "Erweitere die API und Web-UI" in plan["goal"]
    assert [step["position"] for step in plan["steps"]] == [1, 2, 3, 4]
    assert len(plan["risks"]) == 3
    assert len(plan["next_actions"]) == 3
    assert plan["proposal"] == {
        "summary": "Kontrollierte Umsetzung für „Erweitere die API und Web-UI“ vorbereiten.",
        "risk_level": "low",
        "affected_files": ["apps/agent-api/", "apps/web/"],
        "required_approvals": ["human_review"],
    }


def test_task_can_be_retrieved_and_approved() -> None:
    plan = create_plan()

    stored = client.get(f"/agent/tasks/{plan['task_id']}")
    approval = client.post(
        "/agent/approve",
        json={"task_id": plan["task_id"], "decision": "approved"},
    )

    assert stored.status_code == 200
    assert stored.json() == plan
    assert approval.status_code == 200
    assert approval.json()["message"] == "Änderungsvorschlag wurde freigegeben."
    assert approval.json()["task"]["approval_state"] == "approved"


@pytest.mark.parametrize("decision", ["rejected", "needs_changes"])
def test_pending_task_accepts_each_non_approval_decision(decision: str) -> None:
    plan = create_plan("Dokumentation prüfen")

    response = client.post(
        "/agent/approve",
        json={"task_id": plan["task_id"], "decision": decision},
    )

    assert response.status_code == 200
    assert response.json()["task"]["approval_state"] == decision


def test_invalid_approval_value_is_rejected() -> None:
    plan = create_plan()

    response = client.post(
        "/agent/approve",
        json={"task_id": plan["task_id"], "decision": "maybe"},
    )

    assert response.status_code == 422


def test_terminal_approval_state_cannot_be_changed() -> None:
    plan = create_plan()
    client.post(
        "/agent/approve",
        json={"task_id": plan["task_id"], "decision": "rejected"},
    )

    response = client.post(
        "/agent/approve",
        json={"task_id": plan["task_id"], "decision": "approved"},
    )

    assert response.status_code == 409


def test_unknown_task_returns_not_found() -> None:
    response = client.get(f"/agent/tasks/{uuid4()}")

    assert response.status_code == 404
