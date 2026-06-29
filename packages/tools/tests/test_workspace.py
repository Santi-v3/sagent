"""Security boundary tests for workspace paths and bounded reads."""

from pathlib import Path

import pytest

from sagent_tools import FileAccessError, FileTool, WorkspaceGuard, WorkspaceSecurityError


def test_absolute_path_is_blocked_even_when_inside_workspace(tmp_path: Path) -> None:
    guard = WorkspaceGuard(tmp_path)

    with pytest.raises(WorkspaceSecurityError, match="Absolute paths"):
        guard.resolve(tmp_path / "README.md")


@pytest.mark.parametrize("path", ["../outside.txt", "docs/../../outside.txt"])
def test_path_traversal_is_blocked(tmp_path: Path, path: str) -> None:
    guard = WorkspaceGuard(tmp_path)

    with pytest.raises(WorkspaceSecurityError, match="traversal"):
        guard.resolve(path)


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.local",
        ".ssh/id_ed25519",
        "keys/deploy.pem",
        "config/api-token.txt",
        "config/client_secret.json",
        "credentials.json",
    ],
)
def test_sensitive_paths_are_blocked(tmp_path: Path, path: str) -> None:
    guard = WorkspaceGuard(tmp_path)

    with pytest.raises(WorkspaceSecurityError, match="blocked"):
        guard.resolve(path)


def test_symlink_escape_is_blocked(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (outside / "private.txt").write_text("private", encoding="utf-8")
    (workspace / "escape").symlink_to(outside, target_is_directory=True)
    guard = WorkspaceGuard(workspace)

    with pytest.raises(WorkspaceSecurityError, match="escapes"):
        guard.resolve("escape/private.txt", must_exist=True)


def test_read_and_list_only_expose_allowed_text_files(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("hello", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=hidden", encoding="utf-8")
    tool = FileTool(WorkspaceGuard(tmp_path))

    assert tool.read_file("docs/guide.md") == "hello"
    assert tool.list_files() == ["docs/guide.md"]
    with pytest.raises(WorkspaceSecurityError):
        tool.read_file(".env")


def test_binary_and_oversized_files_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "binary.dat").write_bytes(b"text\x00binary")
    (tmp_path / "large.txt").write_text("12345", encoding="utf-8")
    tool = FileTool(WorkspaceGuard(tmp_path), max_file_bytes=4)

    with pytest.raises(FileAccessError, match="Binary"):
        FileTool(WorkspaceGuard(tmp_path)).read_file("binary.dat")
    with pytest.raises(FileAccessError, match="size limit"):
        tool.read_file("large.txt")
