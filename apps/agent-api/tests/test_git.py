"""API tests for bounded Git status, diff, and branch creation."""

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sagent_agent_api.git_integration import get_git_tool
from sagent_agent_api.main import app
from sagent_tools import GitTool, WorkspaceGuard

client = TestClient(app)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("git")
    assert executable is not None
    return subprocess.run(  # noqa: S603 - fixed test repository setup only.
        [executable, "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def git_tool(tmp_path: Path) -> Iterator[GitTool]:
    git(tmp_path, "init", "-b", "main")
    (tmp_path / "README.md").write_text("before\n", encoding="utf-8")
    git(tmp_path, "add", "README.md")
    git(
        tmp_path,
        "-c",
        "user.name=Sagent API Tests",
        "-c",
        "user.email=sagent@example.invalid",
        "commit",
        "-m",
        "chore: initial state",
    )
    tool = GitTool(WorkspaceGuard(tmp_path))
    app.dependency_overrides[get_git_tool] = lambda: tool
    yield tool
    app.dependency_overrides.clear()


def test_status_and_diff_are_structured(git_tool: GitTool) -> None:
    root = git_tool.guard.root
    (root / "README.md").write_text("after\n", encoding="utf-8")

    status_response = client.get("/git/status")
    diff_response = client.get("/git/diff")

    assert status_response.status_code == 200
    assert status_response.json()["branch"] == "main"
    assert status_response.json()["is_main"] is True
    assert status_response.json()["clean"] is False
    assert status_response.json()["files"][0]["path"] == "README.md"
    assert diff_response.status_code == 200
    assert "-before" in diff_response.json()["patch"]
    assert "+after" in diff_response.json()["patch"]
    assert len(diff_response.json()["diff_hash"]) == 64


def test_confirmed_feature_branch_can_be_created(git_tool: GitTool) -> None:
    response = client.post(
        "/git/branch",
        json={
            "name": "feature/api-branch",
            "expected_current_branch": "main",
            "confirmed": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["status"]["branch"] == "feature/api-branch"
    assert response.json()["status"]["is_main"] is False


def test_branch_confirmation_and_policy_are_enforced(git_tool: GitTool) -> None:
    missing_confirmation = client.post(
        "/git/branch",
        json={
            "name": "feature/no-confirmation",
            "expected_current_branch": "main",
            "confirmed": False,
        },
    )
    invalid_name = client.post(
        "/git/branch",
        json={
            "name": "main",
            "expected_current_branch": "main",
            "confirmed": True,
        },
    )

    assert missing_confirmation.status_code == 422
    assert invalid_name.status_code == 422


def test_stale_current_branch_is_rejected(git_tool: GitTool) -> None:
    response = client.post(
        "/git/branch",
        json={
            "name": "feature/stale",
            "expected_current_branch": "another-branch",
            "confirmed": True,
        },
    )

    assert response.status_code == 409
    assert "changed" in response.json()["detail"]


def test_push_and_merge_routes_do_not_exist(git_tool: GitTool) -> None:
    assert client.post("/git/push").status_code == 404
    assert client.post("/git/merge").status_code == 404
