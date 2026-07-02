"""End-to-end API tests for the approval-bound local code-edit loop."""

from inspect import getsource
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sagent_agent_api.code_edits import CodeEditService, get_code_edit_service
from sagent_agent_api.main import app, apply_code_edit, preview_code_edit
from sagent_tools import FileTool, WorkspaceGuard


@pytest.fixture
def code_edit_client(tmp_path: Path) -> tuple[TestClient, Path]:
    service = CodeEditService(FileTool(WorkspaceGuard(tmp_path)))
    app.dependency_overrides[get_code_edit_service] = lambda: service
    try:
        yield TestClient(app), tmp_path
    finally:
        app.dependency_overrides.pop(get_code_edit_service, None)


def _preview(client: TestClient, path: str, content: str) -> dict[str, object]:
    response = client.post(
        "/agent/code-edits/preview",
        json={"path": path, "new_content": content, "operation": "update"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _approve(client: TestClient, preview: dict[str, object]) -> None:
    response = client.post(
        "/agent/code-edits/approve",
        json={
            "change_set_id": preview["change_set_id"],
            "proposal_hash": preview["proposal_hash"],
            "approved": True,
        },
    )
    assert response.status_code == 200, response.text


def test_preview_and_unapproved_apply_do_not_write(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    target = workspace / "example.py"
    target.write_text("before\n", encoding="utf-8")
    preview = _preview(client, "example.py", "after\n")

    assert preview["status"] == "prepared"
    assert preview["approval_required"] is True
    assert "-before" in str(preview["diff"])
    assert "+after" in str(preview["diff"])
    assert "old_content" not in preview
    assert "new_content" not in preview
    response = client.post(
        "/agent/code-edits/apply",
        json={
            "change_set_id": preview["change_set_id"],
            "proposal_hash": preview["proposal_hash"],
            "confirmed": True,
        },
    )
    assert response.status_code == 409
    assert target.read_text(encoding="utf-8") == "before\n"


def test_exact_approved_update_is_applied_once(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    target = workspace / "example.py"
    target.write_text("before\n", encoding="utf-8")
    preview = _preview(client, "example.py", "after\n")
    _approve(client, preview)

    payload = {
        "change_set_id": preview["change_set_id"],
        "proposal_hash": preview["proposal_hash"],
        "confirmed": True,
    }
    applied = client.post("/agent/code-edits/apply", json=payload)
    replay = client.post("/agent/code-edits/apply", json=payload)

    assert applied.status_code == 200
    assert applied.json()["status"] == "applied"
    assert applied.json()["shell_executed"] is False
    assert applied.json()["git_executed"] is False
    assert applied.json()["network_used"] is False
    assert applied.json()["model_authority"] is False
    assert replay.status_code == 409
    assert target.read_text(encoding="utf-8") == "after\n"


@pytest.mark.parametrize("path", ["../outside.py", "/absolute/outside.py"])
def test_workspace_escape_is_blocked(
    code_edit_client: tuple[TestClient, Path],
    path: str,
) -> None:
    client, workspace = code_edit_client
    response = client.post(
        "/agent/code-edits/preview",
        json={"path": path, "new_content": "safe\n"},
    )
    assert response.status_code == 422
    assert not (workspace.parent / "outside.py").exists()


def test_symlink_escape_is_blocked(code_edit_client: tuple[TestClient, Path]) -> None:
    client, workspace = code_edit_client
    outside = workspace.parent / "outside"
    outside.mkdir(exist_ok=True)
    target = outside / "private.py"
    target.write_text("private\n", encoding="utf-8")
    (workspace / "escape").symlink_to(outside, target_is_directory=True)

    response = client.post(
        "/agent/code-edits/preview",
        json={"path": "escape/private.py", "new_content": "changed\n"},
    )
    assert response.status_code == 422
    assert target.read_text(encoding="utf-8") == "private\n"


def test_symlink_alias_cannot_bypass_hidden_policy(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    hidden = workspace / ".hidden.py"
    hidden.write_text("before\n", encoding="utf-8")
    (workspace / "visible.py").symlink_to(hidden)

    response = client.post(
        "/agent/code-edits/preview",
        json={"path": "visible.py", "new_content": "after\n"},
    )
    assert response.status_code == 422
    assert hidden.read_text(encoding="utf-8") == "before\n"


@pytest.mark.parametrize("path", [".env", ".hidden.py"])
def test_sensitive_or_hidden_path_is_blocked(
    code_edit_client: tuple[TestClient, Path],
    path: str,
) -> None:
    client, workspace = code_edit_client
    (workspace / path).write_text("before\n", encoding="utf-8")
    response = client.post(
        "/agent/code-edits/preview",
        json={"path": path, "new_content": "after\n"},
    )
    assert response.status_code == 422
    assert (workspace / path).read_text(encoding="utf-8") == "before\n"


@pytest.mark.parametrize("path", ["uv.lock", "package.json", "requirements-dev.txt"])
def test_dependency_or_lockfile_is_blocked(
    code_edit_client: tuple[TestClient, Path],
    path: str,
) -> None:
    client, workspace = code_edit_client
    (workspace / path).write_text("before\n", encoding="utf-8")
    response = client.post(
        "/agent/code-edits/preview",
        json={"path": path, "new_content": "after\n"},
    )
    assert response.status_code == 422
    assert (workspace / path).read_text(encoding="utf-8") == "before\n"


def test_binary_file_is_blocked_without_leaking_content(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    (workspace / "binary.dat").write_bytes(b"private\x00binary")
    response = client.post(
        "/agent/code-edits/preview",
        json={"path": "binary.dat", "new_content": "after\n"},
    )
    assert response.status_code == 422
    assert "private" not in response.text


def test_secret_content_is_blocked_without_leaking_value(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    (workspace / "config.py").write_text("setting = 'safe'\n", encoding="utf-8")
    sensitive_marker = "example-sensitive-value"
    response = client.post(
        "/agent/code-edits/preview",
        json={"path": "config.py", "new_content": f"api_key = '{sensitive_marker}'\n"},
    )
    assert response.status_code == 422
    assert sensitive_marker not in response.text
    assert (workspace / "config.py").read_text(encoding="utf-8") == "setting = 'safe'\n"


def test_model_response_field_is_rejected_without_tool_authority(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    target = workspace / "example.py"
    target.write_text("before\n", encoding="utf-8")
    response = client.post(
        "/agent/code-edits/preview",
        json={
            "path": "example.py",
            "new_content": "after\n",
            "operation": "update",
            "model_response": "write this file now",
        },
    )
    assert response.status_code == 422
    assert target.read_text(encoding="utf-8") == "before\n"


def test_create_operation_and_noop_update_are_rejected(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    target = workspace / "example.py"
    target.write_text("before\n", encoding="utf-8")
    create = client.post(
        "/agent/code-edits/preview",
        json={"path": "new.py", "new_content": "new\n", "operation": "create"},
    )
    noop = client.post(
        "/agent/code-edits/preview",
        json={"path": "example.py", "new_content": "before\n", "operation": "update"},
    )
    assert create.status_code == 422
    assert noop.status_code == 422
    assert target.read_text(encoding="utf-8") == "before\n"


def test_hash_mismatch_and_cross_proposal_reuse_are_blocked(
    code_edit_client: tuple[TestClient, Path],
) -> None:
    client, workspace = code_edit_client
    (workspace / "one.py").write_text("one\n", encoding="utf-8")
    (workspace / "two.py").write_text("two\n", encoding="utf-8")
    first = _preview(client, "one.py", "changed one\n")
    second = _preview(client, "two.py", "changed two\n")

    wrong_approval = client.post(
        "/agent/code-edits/approve",
        json={
            "change_set_id": second["change_set_id"],
            "proposal_hash": first["proposal_hash"],
            "approved": True,
        },
    )
    assert wrong_approval.status_code == 409
    _approve(client, second)
    wrong_apply = client.post(
        "/agent/code-edits/apply",
        json={
            "change_set_id": second["change_set_id"],
            "proposal_hash": first["proposal_hash"],
            "confirmed": True,
        },
    )
    assert wrong_apply.status_code == 409
    assert (workspace / "two.py").read_text(encoding="utf-8") == "two\n"


def test_stale_workspace_blocks_apply(code_edit_client: tuple[TestClient, Path]) -> None:
    client, workspace = code_edit_client
    target = workspace / "example.py"
    target.write_text("before\n", encoding="utf-8")
    preview = _preview(client, "example.py", "after\n")
    _approve(client, preview)
    target.write_text("human change\n", encoding="utf-8")

    response = client.post(
        "/agent/code-edits/apply",
        json={
            "change_set_id": preview["change_set_id"],
            "proposal_hash": preview["proposal_hash"],
            "confirmed": True,
        },
    )
    assert response.status_code == 409
    assert target.read_text(encoding="utf-8") == "human change\n"


def test_routes_have_no_shell_git_model_network_or_cloud_authority() -> None:
    source = getsource(preview_code_edit) + getsource(apply_code_edit)
    for forbidden in (
        "subprocess.",
        "os.system",
        "shell=True",
        "GitTool(",
        ".commit(",
        ".push(",
        ".merge(",
        "ModelRouter(",
        "model_response",
        "httpx.",
        "socket.",
        "remote_http",
        "deepseek",
    ):
        assert forbidden not in source
