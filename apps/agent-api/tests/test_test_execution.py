"""API tests for approved, allowlist-only test execution."""

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sagent_agent_api.main import app
from sagent_agent_api.test_execution import get_test_runner
from sagent_tools import TestProfile as RunnerProfile
from sagent_tools import TestRunner as Runner
from sagent_tools import WorkspaceGuard

client = TestClient(app)


def make_profile(profile_id: str, script: str) -> RunnerProfile:
    return RunnerProfile(
        profile_id=profile_id,
        command=f"python:{profile_id}",
        argv=(str(Path(sys.executable).resolve()), "-c", script),
        timeout_seconds=2,
    )


@pytest.fixture
def runner(tmp_path: Path) -> Iterator[Runner]:
    test_runner = Runner(
        WorkspaceGuard(tmp_path),
        [
            make_profile("success", "print('all good')"),
            make_profile("failure", "import sys; print('failed'); sys.exit(2)"),
        ],
    )
    app.dependency_overrides[get_test_runner] = lambda: test_runner
    yield test_runner
    app.dependency_overrides.clear()


def approved_task() -> str:
    plan = client.post("/agent/plan", json={"task": "Sichere Tests ausführen"}).json()
    approval = client.post(
        "/agent/approve",
        json={"task_id": plan["task_id"], "decision": "approved"},
    )
    assert approval.status_code == 200
    return str(plan["task_id"])


def run_payload(task_id: str, profile_id: str) -> dict[str, object]:
    return {
        "task_id": task_id,
        "profile_id": profile_id,
        "expected_command": f"python:{profile_id}",
        "confirmed": True,
    }


def test_successful_run_is_stored_and_retrievable(runner: Runner) -> None:
    task_id = approved_task()

    profiles = client.get("/agent/test-profiles")
    response = client.post("/agent/run-tests", json=run_payload(task_id, "success"))

    assert profiles.status_code == 200
    assert profiles.json()[0]["command"] == "python:success"
    assert response.status_code == 200
    result = response.json()
    assert result["passed"] is True
    assert result["exit_code"] == 0
    assert result["stdout"] == "all good\n"
    stored = client.get(f"/agent/test-results/{result['result_id']}")
    assert stored.status_code == 200
    assert stored.json() == result


def test_failed_run_returns_logs_without_becoming_an_api_error(runner: Runner) -> None:
    response = client.post(
        "/agent/run-tests",
        json=run_payload(approved_task(), "failure"),
    )

    assert response.status_code == 200
    assert response.json()["passed"] is False
    assert response.json()["exit_code"] == 2
    assert response.json()["stdout"] == "failed\n"


def test_pending_task_cannot_start_tests(runner: Runner) -> None:
    plan = client.post("/agent/plan", json={"task": "Noch nicht freigegeben"}).json()

    response = client.post(
        "/agent/run-tests",
        json=run_payload(str(plan["task_id"]), "success"),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Task must be approved before tests can run."


def test_forbidden_profile_is_blocked(runner: Runner) -> None:
    payload = run_payload(approved_task(), "rm-everything")
    payload["expected_command"] = "rm -rf /"

    response = client.post("/agent/run-tests", json=payload)

    assert response.status_code == 403
    assert "not allowlisted" in response.json()["detail"]


def test_changed_display_command_is_blocked(runner: Runner) -> None:
    payload = run_payload(approved_task(), "success")
    payload["expected_command"] = "python:tampered"

    response = client.post("/agent/run-tests", json=payload)

    assert response.status_code == 409
    assert "does not match" in response.json()["detail"]


def test_explicit_confirmation_is_required(runner: Runner) -> None:
    payload = run_payload(approved_task(), "success")
    payload["confirmed"] = False

    response = client.post("/agent/run-tests", json=payload)

    assert response.status_code == 422


def test_unknown_result_returns_not_found(runner: Runner) -> None:
    response = client.get("/agent/test-results/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
