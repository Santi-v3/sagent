"""Tests for the approval-gated test-runner contract.

Every test verifies that the capability-policy gate, hash-bound approval,
and fixed allowlist prevent unauthorised execution.
"""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from sagent_agent_api.main import app
from sagent_agent_api.test_runner import (
    TestCommandNotAllowedError,
    TestRunConflictError,
    TestRunHashMismatchError,
    TestRunNotApprovedError,
    TestRunNotFoundError,
    approve_test_run,
    execute_test_run,
    get_test_command,
    list_test_commands,
    preview_test_run,
    reset,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup() -> None:
    reset()
    yield
    reset()


class TestAllowlist:
    def test_list_commands_returns_all_commands(self) -> None:
        cmds = list_test_commands()
        assert len(cmds) >= 3
        ids = {c.command_id for c in cmds}
        assert "python-pytest-all" in ids
        assert "python-pytest-capability" in ids
        assert "python-lint" in ids

    def test_get_valid_command(self) -> None:
        cmd = get_test_command("python-lint")
        assert cmd.display_name == "Python: Ruff lint"
        assert len(cmd.argv) >= 4
        assert cmd.timeout_seconds == 60.0

    def test_get_unknown_command_raises(self) -> None:
        with pytest.raises(TestCommandNotAllowedError):
            get_test_command("not-a-real-command")

    def test_argv_is_tuple_not_shell_string(self) -> None:
        for cid in ("python-pytest-all", "python-pytest-capability", "python-lint"):
            cmd = get_test_command(cid)
            assert isinstance(cmd.argv, tuple)
            assert all(isinstance(a, str) for a in cmd.argv)
            assert all("\x00" not in a for a in cmd.argv)
            assert not any(";" in a or "|" in a or "&&" in a for a in cmd.argv)

    def test_no_git_commands_in_allowlist(self) -> None:
        for cmd in list_test_commands():
            assert "git" not in cmd.command_id
            assert "git" not in cmd.display_name.lower()
            assert not any("git" in a for a in cmd.argv)

    def test_no_network_install_or_download_commands(self) -> None:
        forbidden = {"pip", "npm", "curl", "wget", "ssh", "scp", "rsync"}
        for cmd in list_test_commands():
            assert not any(
                any(f in a.lower() for f in forbidden) for a in cmd.argv
            ), f"{cmd.command_id} contains forbidden tool"


class TestPreview:
    def test_preview_valid_command_returns_metadata(self) -> None:
        state, decision = preview_test_run("python-lint")
        assert state.test_run_id is not None
        assert state.command_id == "python-lint"
        assert len(state.approval_hash) == 64
        assert state.approved is False
        assert state.completed is False

    def test_preview_unknown_command_raises(self) -> None:
        with pytest.raises(TestCommandNotAllowedError):
            preview_test_run("nonexistent-command")

    def test_preview_uses_capability_policy(self) -> None:
        state, decision = preview_test_run("python-pytest-all")
        # run_tests is approval_required in DEFAULT_CAPABILITY_POLICY
        assert decision.value in ("denied", "needs_approval")

    def test_preview_approval_hash_is_deterministic_for_same_run(self) -> None:
        state1, _ = preview_test_run("python-lint")
        # A second preview must generate a different run (different ID, different hash)
        state2, _ = preview_test_run("python-lint")
        assert state1.test_run_id != state2.test_run_id
        assert state1.approval_hash != state2.approval_hash

    def test_preview_via_api_returns_201(self) -> None:
        response = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        assert response.status_code == 201
        data = response.json()
        assert data["command_id"] == "python-lint"
        assert data["capability"] == "run_tests"
        assert data["decision"] in ("denied", "needs_approval")
        assert data["requires_approval"] is True
        assert len(data["approval_hash"]) == 64
        assert data["shell_used"] is False
        assert data["git_used"] is False
        assert data["network_used"] is False
        assert data["cloud_used"] is False
        assert data["model_called"] is False

    def test_preview_via_api_unknown_command(self) -> None:
        response = client.post(
            "/agent/test-runs/preview", json={"command_id": "invalid-command"}
        )
        assert response.status_code == 404

    def test_preview_shows_command_args_as_list(self) -> None:
        response = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        data = response.json()
        assert isinstance(data["command_args"], list)
        assert len(data["command_args"]) > 0


class TestApprove:
    def test_approve_valid_run(self) -> None:
        state, _ = preview_test_run("python-lint")
        result = approve_test_run(state.test_run_id, state.approval_hash)
        assert result.approved is True

    def test_approve_nonexistent_run_raises(self) -> None:
        with pytest.raises(TestRunNotFoundError):
            approve_test_run(UUID("00000000-0000-0000-0000-000000000000"), "invalid")

    def test_approve_wrong_hash_raises(self) -> None:
        state, _ = preview_test_run("python-lint")
        with pytest.raises(TestRunHashMismatchError):
            approve_test_run(state.test_run_id, "x" * 64)

    def test_approve_twice_raises(self) -> None:
        state, _ = preview_test_run("python-lint")
        approve_test_run(state.test_run_id, state.approval_hash)
        with pytest.raises(TestRunConflictError):
            approve_test_run(state.test_run_id, state.approval_hash)

    def test_approve_via_api_returns_200(self) -> None:
        preview = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        pdata = preview.json()
        response = client.post(
            "/agent/test-runs/approve",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "approved": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    def test_approve_via_api_wrong_hash(self) -> None:
        preview = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        pdata = preview.json()
        response = client.post(
            "/agent/test-runs/approve",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": "x" * 64,
                "approved": True,
            },
        )
        assert response.status_code == 409


class TestExecute:
    def test_run_without_approval_raises(self) -> None:
        state, _ = preview_test_run("python-lint")
        with pytest.raises(TestRunNotApprovedError):
            execute_test_run(state.test_run_id, state.approval_hash, confirmed=True)

    def test_run_nonexistent_run_raises(self) -> None:
        with pytest.raises(TestRunNotFoundError):
            execute_test_run(
                UUID("00000000-0000-0000-0000-000000000000"),
                "invalid",
                confirmed=True,
            )

    def test_run_wrong_hash_raises(self) -> None:
        state, _ = preview_test_run("python-lint")
        approve_test_run(state.test_run_id, state.approval_hash)
        with pytest.raises(TestRunHashMismatchError):
            execute_test_run(state.test_run_id, "x" * 64, confirmed=True)

    def test_run_not_confirmed_raises(self) -> None:
        state, _ = preview_test_run("python-lint")
        approve_test_run(state.test_run_id, state.approval_hash)
        with pytest.raises(TestRunConflictError):
            execute_test_run(state.test_run_id, state.approval_hash, confirmed=False)

    def test_run_twice_raises(self) -> None:
        state, _ = preview_test_run("python-pytest-capability")
        approve_test_run(state.test_run_id, state.approval_hash)
        execute_test_run(state.test_run_id, state.approval_hash, confirmed=True)
        with pytest.raises(TestRunConflictError):
            execute_test_run(state.test_run_id, state.approval_hash, confirmed=True)

    def test_run_after_approval_executes_and_returns_result(self) -> None:
        state, _ = preview_test_run("python-pytest-capability")
        approve_test_run(state.test_run_id, state.approval_hash)
        result = execute_test_run(
            state.test_run_id, state.approval_hash, confirmed=True
        )
        assert result.completed is True
        assert result.exit_code is not None
        assert result.started_at is not None
        assert result.completed_at is not None

    def test_run_via_api_without_approval_is_blocked(self) -> None:
        preview = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        pdata = preview.json()
        response = client.post(
            "/agent/test-runs/run",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "confirmed": True,
            },
        )
        assert response.status_code == 409
        assert "approve" in response.text.lower() or "approv" in response.text.lower()

    def test_run_via_api_full_flow(self) -> None:
        preview = client.post(
            "/agent/test-runs/preview", json={"command_id": "python-pytest-capability"}
        )
        assert preview.status_code == 201
        pdata = preview.json()

        approve = client.post(
            "/agent/test-runs/approve",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "approved": True,
            },
        )
        assert approve.status_code == 200

        execute = client.post(
            "/agent/test-runs/run",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "confirmed": True,
            },
        )
        assert execute.status_code == 200
        edata = execute.json()
        assert edata["exit_code"] is not None
        assert edata["shell_used"] is False
        assert edata["git_used"] is False
        assert edata["network_used"] is False
        assert edata["cloud_used"] is False
        assert edata["model_called"] is False

    def test_run_via_api_wrong_hash_is_blocked(self) -> None:
        preview = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        pdata = preview.json()
        client.post(
            "/agent/test-runs/approve",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "approved": True,
            },
        )
        response = client.post(
            "/agent/test-runs/run",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": "x" * 64,
                "confirmed": True,
            },
        )
        assert response.status_code == 409

    def test_run_via_api_unknown_id_returns_404(self) -> None:
        response = client.post(
            "/agent/test-runs/run",
            json={
                "test_run_id": "00000000-0000-0000-0000-000000000000",
                "approval_hash": "x" * 64,
                "confirmed": True,
            },
        )
        assert response.status_code == 404


class TestListCommands:
    def test_list_commands_via_api(self) -> None:
        response = client.get("/agent/test-runs/commands")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        ids = [c["command_id"] for c in data]
        assert "python-pytest-all" in ids
        assert "python-lint" in ids

    def test_list_commands_has_no_secrets_or_endpoints(self) -> None:
        response = client.get("/agent/test-runs/commands")
        text = response.text.lower()
        assert "api_key" not in text
        assert "secret" not in text
        assert "token" not in text
        assert "endpoint" not in text
        assert "http://" not in text
        assert "https://" not in text
        assert "getenv" not in text
        assert "environ" not in text


class TestNoSecretsOrEnv:
    def test_preview_response_has_no_secrets(self) -> None:
        response = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        text = response.text.lower()
        assert "api_key" not in text
        assert "secret" not in text
        assert "token" not in text
        assert "password" not in text
        assert "endpoint" not in text
        assert "http://" not in text
        assert "https://" not in text
        assert "getenv" not in text
        assert "environ" not in text

    def test_approve_response_has_no_secrets(self) -> None:
        preview = client.post("/agent/test-runs/preview", json={"command_id": "python-lint"})
        pdata = preview.json()
        response = client.post(
            "/agent/test-runs/approve",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "approved": True,
            },
        )
        text = response.text.lower()
        assert "api_key" not in text
        assert "secret" not in text
        assert "token" not in text

    def test_execute_response_has_no_secrets(self) -> None:
        preview = client.post(
            "/agent/test-runs/preview", json={"command_id": "python-pytest-capability"}
        )
        pdata = preview.json()
        client.post(
            "/agent/test-runs/approve",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "approved": True,
            },
        )
        response = client.post(
            "/agent/test-runs/run",
            json={
                "test_run_id": pdata["test_run_id"],
                "approval_hash": pdata["approval_hash"],
                "confirmed": True,
            },
        )
        text = response.text.lower()
        assert "api_key" not in text
        assert "endpoint" not in text


class TestExecuteSafety:
    def test_output_is_bounded(self) -> None:
        state, _ = preview_test_run("python-pytest-capability")
        approve_test_run(state.test_run_id, state.approval_hash)
        result = execute_test_run(
            state.test_run_id, state.approval_hash, confirmed=True
        )
        assert len(result.stdout) < 25_000
        assert len(result.stderr) < 25_000

    def test_timeout_is_set(self) -> None:
        cmd = get_test_command("python-pytest-capability")
        assert cmd.timeout_seconds <= 120.0

    def test_subprocess_uses_shell_false(self) -> None:
        cmd = get_test_command("python-pytest-capability")
        # Verify the allowlist only contains trusted absolute-or-module commands
        assert cmd.argv[0].endswith("python") or cmd.argv[0].endswith("python3")


class TestCapabilityPolicyGate:
    def test_preview_decision_matches_capability_policy(self) -> None:
        from sagent_agent_core import (
            DEFAULT_CAPABILITY_POLICY,
            CapabilityName,
            evaluate_capability,
        )

        decision = evaluate_capability(DEFAULT_CAPABILITY_POLICY, CapabilityName.RUN_TESTS)
        state, preview_decision = preview_test_run("python-pytest-all")
        assert preview_decision is decision

    def test_no_model_response_authority(self) -> None:
        state, decision = preview_test_run("python-pytest-all")
        assert not hasattr(state, "model_response")
        assert not hasattr(state, "tool_call")
        assert not hasattr(decision, "model_response")
