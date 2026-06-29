"""Security and behavior tests for the bounded local Git tool."""

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from sagent_tools import (
    GitBranchPolicyError,
    GitOperationBlockedError,
    GitRepositoryError,
    GitStateConflictError,
    GitTool,
    WorkspaceGuard,
)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("git")
    assert executable is not None
    return subprocess.run(  # noqa: S603 - fixed test setup commands only.
        [executable, "-C", str(root), *args],
        check=check,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repository(tmp_path: Path) -> Iterator[tuple[Path, GitTool]]:
    git(tmp_path, "init", "-b", "main")
    (tmp_path / "README.md").write_text("before\n", encoding="utf-8")
    git(tmp_path, "add", "README.md")
    git(
        tmp_path,
        "-c",
        "user.name=Sagent Tests",
        "-c",
        "user.email=sagent@example.invalid",
        "commit",
        "-m",
        "chore: initial state",
    )
    yield tmp_path, GitTool(WorkspaceGuard(tmp_path))


def test_status_warns_on_clean_main_branch(repository: tuple[Path, GitTool]) -> None:
    _, tool = repository

    status = tool.status()

    assert status.branch == "main"
    assert status.is_main is True
    assert status.clean is True
    assert status.detached is False
    assert status.files == ()
    assert status.warning is not None


def test_diff_includes_tracked_and_untracked_text_files(
    repository: tuple[Path, GitTool],
) -> None:
    root, tool = repository
    (root / "README.md").write_text("after\n", encoding="utf-8")
    (root / "new.txt").write_text("new\n", encoding="utf-8")

    status = tool.status()
    diff = tool.diff()

    assert status.clean is False
    assert {file.path for file in status.files} == {"README.md", "new.txt"}
    assert "-before" in diff.patch
    assert "+after" in diff.patch
    assert "--- /dev/null" in diff.patch
    assert "+new" in diff.patch
    assert diff.file_count == 2
    assert diff.truncated is False


def test_diff_separates_staged_unstaged_and_empty_files(
    repository: tuple[Path, GitTool],
) -> None:
    root, tool = repository
    (root / "README.md").write_text("staged\n", encoding="utf-8")
    git(root, "add", "README.md")
    (root / "README.md").write_text("unstaged\n", encoding="utf-8")
    (root / "empty.txt").write_text("", encoding="utf-8")

    diff = tool.diff()

    assert "# Staged changes" in diff.patch
    assert "# Unstaged changes" in diff.patch
    assert "+staged" in diff.patch
    assert "+unstaged" in diff.patch
    assert "diff --git a/empty.txt b/empty.txt" in diff.patch
    assert "+++ b/empty.txt" in diff.patch


def test_many_untracked_files_keep_diff_output_bounded(
    repository: tuple[Path, GitTool],
) -> None:
    root, _ = repository
    tool = GitTool(WorkspaceGuard(root), max_output_bytes=160)
    for index in range(10):
        (root / f"file-{index}.txt").write_text("x" * 32, encoding="utf-8")

    diff = tool.diff()

    assert diff.truncated is True
    assert len(diff.patch.encode("utf-8")) <= 200
    assert "[Sagent: Git diff truncated]" in diff.patch


def test_only_valid_feature_branch_can_be_created(repository: tuple[Path, GitTool]) -> None:
    _, tool = repository

    status = tool.create_branch("feature/safe-git", "main")

    assert status.branch == "feature/safe-git"
    assert status.is_main is False
    with pytest.raises(GitStateConflictError, match="changed"):
        tool.create_branch("feature/another", "main")
    with pytest.raises(GitBranchPolicyError, match="must use"):
        tool.create_branch("main", "feature/safe-git")


def test_commit_preparation_never_stages_commits_or_pushes(
    repository: tuple[Path, GitTool],
) -> None:
    root, tool = repository
    tool.create_branch("feature/prepare", "main")
    (root / "README.md").write_text("after\n", encoding="utf-8")
    before_head = git(root, "rev-parse", "HEAD").stdout.strip()
    visible_diff = tool.diff()

    preparation = tool.prepare_commit(
        "feat: prepare safe change",
        visible_diff.diff_hash,
    )

    assert preparation.branch == "feature/prepare"
    assert preparation.diff_hash == visible_diff.diff_hash
    assert preparation.push_allowed is False
    assert preparation.merge_allowed is False
    assert git(root, "diff", "--cached").stdout == ""
    assert git(root, "rev-parse", "HEAD").stdout.strip() == before_head
    with pytest.raises(GitOperationBlockedError, match="push"):
        tool.push()
    with pytest.raises(GitOperationBlockedError, match="merge"):
        tool.merge()


def test_commit_preparation_is_blocked_on_main_and_stale_diff(
    repository: tuple[Path, GitTool],
) -> None:
    root, tool = repository
    (root / "README.md").write_text("first\n", encoding="utf-8")
    main_diff = tool.diff()

    with pytest.raises(GitBranchPolicyError, match="protected"):
        tool.prepare_commit("feat: not on main", main_diff.diff_hash)

    tool.create_branch("feature/stale", "main")
    visible_diff = tool.diff()
    (root / "README.md").write_text("second\n", encoding="utf-8")
    with pytest.raises(GitStateConflictError, match="changed"):
        tool.prepare_commit("feat: stale proposal", visible_diff.diff_hash)


def test_sensitive_paths_and_secret_content_block_preparation(
    repository: tuple[Path, GitTool],
) -> None:
    root, tool = repository
    tool.create_branch("feature/secrets", "main")
    (root / ".env").write_text("TOKEN=private-value\n", encoding="utf-8")
    (root / "config.txt").write_text("token=private-value\n", encoding="utf-8")

    status = tool.status()
    diff = tool.diff()

    assert any(file.sensitive and file.path == "[sensitive path hidden]" for file in status.files)
    assert ".env" not in diff.patch
    assert "private-value" not in diff.patch
    assert "token=[REDACTED]" in diff.patch
    assert diff.sensitive_paths_hidden == 1
    assert diff.secrets_redacted is True
    with pytest.raises(GitStateConflictError, match="secrets|sensitive"):
        tool.prepare_commit("feat: unsafe secrets", diff.diff_hash)


def test_workspace_must_equal_repository_root(tmp_path: Path) -> None:
    git(tmp_path, "init", "-b", "main")
    nested = tmp_path / "nested"
    nested.mkdir()

    with pytest.raises(GitRepositoryError, match="must equal"):
        GitTool(WorkspaceGuard(nested))
