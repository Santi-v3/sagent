"""Bounded Git inspection and narrowly scoped local branch operations."""

import difflib
import hashlib
import hmac
import os
import re
import shutil
import signal
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Thread
from time import monotonic
from typing import BinaryIO
from uuid import UUID, uuid4

from sagent_tools.files import FileAccessError, FileTool
from sagent_tools.redaction import redact_secrets
from sagent_tools.workspace import WorkspaceGuard, WorkspaceSecurityError


class GitRepositoryError(ValueError):
    """Raised when the workspace is not exactly one supported Git repository."""


class GitCommandError(RuntimeError):
    """Raised when a fixed local Git command fails or exceeds its limits."""


class GitBranchPolicyError(ValueError):
    """Raised when a branch transition violates the feature-branch policy."""


class GitStateConflictError(ValueError):
    """Raised when Git state changed after it was shown to the user."""


class GitOperationBlockedError(PermissionError):
    """Raised for Git operations that this MVP intentionally cannot execute."""


@dataclass(frozen=True, slots=True)
class GitFileStatus:
    """One bounded and optionally redacted worktree status entry."""

    path: str
    index_status: str
    worktree_status: str
    original_path: str | None = None
    sensitive: bool = False


@dataclass(frozen=True, slots=True)
class GitStatus:
    """Structured status for one fixed local repository."""

    branch: str | None
    detached: bool
    is_main: bool
    clean: bool
    ahead: int
    behind: int
    head_sha: str | None
    files: tuple[GitFileStatus, ...]
    warning: str | None


@dataclass(frozen=True, slots=True)
class GitDiff:
    """Reviewable staged, unstaged, and untracked diff output."""

    patch: str
    diff_hash: str
    file_count: int
    truncated: bool
    secrets_redacted: bool
    sensitive_paths_hidden: int


@dataclass(frozen=True, slots=True)
class CommitPreparation:
    """A non-executing commit plan bound to one exact visible diff."""

    preparation_id: UUID
    branch: str
    message: str
    diff_hash: str
    files: tuple[str, ...]
    created_at: datetime
    push_allowed: bool = False
    merge_allowed: bool = False


@dataclass(frozen=True, slots=True)
class _RawStatusEntry:
    path: str
    index_status: str
    worktree_status: str
    original_path: str | None = None


class _BoundedBytes:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.data = bytearray()
        self.truncated = False

    def drain(self, stream: BinaryIO) -> None:
        try:
            while chunk := stream.read(8_192):
                remaining = self.limit - len(self.data)
                if remaining > 0:
                    self.data.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    self.truncated = True
        finally:
            stream.close()


class GitTool:
    """Inspect Git safely and create only validated local feature branches."""

    _FEATURE_BRANCH = re.compile(
        r"^(?:codex|feature|fix|docs|test|chore)/[a-z0-9][a-z0-9._-]{0,79}$"
    )
    _CONVENTIONAL_COMMIT = re.compile(
        r"^(?:build|chore|ci|docs|feat|fix|perf|refactor|style|test)"
        r"(?:\([a-z0-9._-]+\))?!?: .{1,72}$"
    )
    _PROTECTED_BRANCHES = frozenset({"main", "master", "trunk"})
    _HIDDEN_PATH = "[sensitive path hidden]"

    def __init__(
        self,
        guard: WorkspaceGuard,
        *,
        git_executable: str | Path | None = None,
        max_output_bytes: int = 524_288,
        timeout_seconds: float = 10.0,
        max_status_entries: int = 2_000,
    ) -> None:
        if max_output_bytes < 1 or timeout_seconds <= 0 or max_status_entries < 1:
            raise ValueError("Git resource limits must be positive.")
        executable = Path(git_executable or shutil.which("git") or "")
        if not executable.is_absolute() or not executable.is_file():
            raise GitRepositoryError("A trusted absolute Git executable is required.")
        self.guard = guard
        self.git_executable = executable
        self.max_output_bytes = max_output_bytes
        self.timeout_seconds = timeout_seconds
        self.max_status_entries = max_status_entries
        self.file_tool = FileTool(guard, max_file_bytes=min(max_output_bytes, 1_048_576))

        top_level = self._run_git(["rev-parse", "--show-toplevel"]).stdout_text.strip()
        try:
            resolved_top_level = Path(top_level).resolve(strict=True)
        except OSError as error:
            raise GitRepositoryError("Git repository root could not be resolved.") from error
        if resolved_top_level != self.guard.root:
            raise GitRepositoryError("Workspace root must equal the Git repository root.")

    def status(self) -> GitStatus:
        """Return branch and file state without taking optional Git locks."""

        branch = self._current_branch()
        detached = branch is None
        is_main = branch in self._PROTECTED_BRANCHES
        head_result = self._run_git(
            ["rev-parse", "--verify", "HEAD"],
            allowed_returncodes=(0, 128),
        )
        head_sha = head_result.stdout_text.strip() or None
        ahead, behind = self._ahead_behind()
        entries = self._raw_status()
        files = tuple(self._public_status(entry) for entry in entries)

        warning = None
        if is_main:
            warning = "Protected branch: create a feature branch before preparing changes."
        elif detached:
            warning = "Detached HEAD: create a feature branch before preparing changes."

        return GitStatus(
            branch=branch,
            detached=detached,
            is_main=is_main,
            clean=not entries,
            ahead=ahead,
            behind=behind,
            head_sha=head_sha,
            files=files,
            warning=warning,
        )

    def diff(self) -> GitDiff:
        """Return a bounded, redacted review diff for all non-sensitive changes."""

        entries = self._raw_status()
        sensitive_entries = [entry for entry in entries if self._entry_is_sensitive(entry)]
        safe_entries = [entry for entry in entries if not self._entry_is_sensitive(entry)]
        staged_paths = self._paths_for(safe_entries, staged=True)
        unstaged_paths = self._paths_for(safe_entries, staged=False)
        untracked_paths = sorted(entry.path for entry in safe_entries if self._is_untracked(entry))

        sections: list[str] = []
        command_truncated = False
        if staged_paths:
            staged = self._run_git(
                [
                    "diff",
                    "--cached",
                    "--no-color",
                    "--no-ext-diff",
                    "--no-textconv",
                    "--ignore-submodules=all",
                    "--",
                    *staged_paths,
                ],
                allow_truncation=True,
            )
            command_truncated = command_truncated or staged.truncated
            if staged.stdout_text:
                sections.append("# Staged changes\n" + staged.stdout_text)

        if unstaged_paths:
            unstaged = self._run_git(
                [
                    "diff",
                    "--no-color",
                    "--no-ext-diff",
                    "--no-textconv",
                    "--ignore-submodules=all",
                    "--",
                    *unstaged_paths,
                ],
                allow_truncation=True,
            )
            command_truncated = command_truncated or unstaged.truncated
            if unstaged.stdout_text:
                sections.append("# Unstaged changes\n" + unstaged.stdout_text)

        untracked_parts: list[str] = []
        untracked_bytes = 0
        for path in untracked_paths:
            untracked_diff = self._untracked_diff(path)
            encoded_size = len(untracked_diff.encode("utf-8"))
            if untracked_parts and untracked_bytes + encoded_size > self.max_output_bytes * 2:
                command_truncated = True
                break
            untracked_parts.append(untracked_diff)
            untracked_bytes += encoded_size
        untracked_text = "".join(untracked_parts)
        if untracked_text:
            sections.append("# Untracked files\n" + untracked_text)

        raw_patch = "\n".join(sections)
        redacted_patch, secrets_redacted = redact_secrets(raw_patch)
        patch, combined_truncated = self._truncate_text(redacted_patch)
        truncated = command_truncated or combined_truncated
        if truncated:
            patch = f"{patch}\n[Sagent: Git diff truncated]"
        diff_hash = hashlib.sha256(patch.encode("utf-8")).hexdigest()
        return GitDiff(
            patch=patch,
            diff_hash=diff_hash,
            file_count=len(entries),
            truncated=truncated,
            secrets_redacted=secrets_redacted,
            sensitive_paths_hidden=len(sensitive_entries),
        )

    def create_branch(self, name: str, expected_current_branch: str | None) -> GitStatus:
        """Create one validated local feature branch after a state comparison."""

        current = self._current_branch()
        if current != expected_current_branch:
            raise GitStateConflictError("Current branch changed after it was displayed.")
        if not self._FEATURE_BRANCH.fullmatch(name):
            raise GitBranchPolicyError(
                "Branch must use codex/, feature/, fix/, docs/, test/, or chore/."
            )
        check = self._run_git(
            ["check-ref-format", "--branch", name],
            allowed_returncodes=(0, 1),
        )
        if check.returncode != 0:
            raise GitBranchPolicyError("Branch name is not a valid Git reference.")
        exists = self._run_git(
            ["show-ref", "--verify", "--quiet", f"refs/heads/{name}"],
            allowed_returncodes=(0, 1),
        )
        if exists.returncode == 0:
            raise GitBranchPolicyError("Branch already exists.")

        self._run_git(["switch", "-c", name], mutating=True)
        return self.status()

    def prepare_commit(self, message: str, expected_diff_hash: str) -> CommitPreparation:
        """Prepare metadata for review without staging or committing anything."""

        current_status = self.status()
        if current_status.branch is None or current_status.is_main:
            raise GitBranchPolicyError("Commit preparation is blocked on a protected branch.")
        if not self._CONVENTIONAL_COMMIT.fullmatch(message):
            raise GitBranchPolicyError(
                "Commit message must be a single Conventional Commit subject."
            )
        current_diff = self.diff()
        if not hmac.compare_digest(current_diff.diff_hash, expected_diff_hash):
            raise GitStateConflictError("Git diff changed after it was displayed.")
        if current_diff.truncated:
            raise GitStateConflictError("Truncated diffs cannot be prepared for commit.")
        if current_diff.secrets_redacted or current_diff.sensitive_paths_hidden:
            raise GitStateConflictError(
                "Potential secrets or sensitive paths block commit preparation."
            )
        if not current_diff.patch:
            raise GitStateConflictError("No reviewable changes are available.")

        files = tuple(file.path for file in current_status.files if not file.sensitive)
        return CommitPreparation(
            preparation_id=uuid4(),
            branch=current_status.branch,
            message=message,
            diff_hash=current_diff.diff_hash,
            files=files,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def push() -> None:
        """Keep all network writes unavailable in MVP 1.E."""

        raise GitOperationBlockedError("Git push is unavailable without a separate approval flow.")

    @staticmethod
    def merge() -> None:
        """Keep branch integration unavailable in MVP 1.E."""

        raise GitOperationBlockedError("Git merge is unavailable without explicit human approval.")

    def _current_branch(self) -> str | None:
        result = self._run_git(
            ["symbolic-ref", "--quiet", "--short", "HEAD"],
            allowed_returncodes=(0, 1),
        )
        return result.stdout_text.strip() or None

    def _ahead_behind(self) -> tuple[int, int]:
        result = self._run_git(
            ["rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
            allowed_returncodes=(0, 128),
        )
        if result.returncode != 0 or not result.stdout_text.strip():
            return 0, 0
        try:
            behind_text, ahead_text = result.stdout_text.split()
            return int(ahead_text), int(behind_text)
        except (TypeError, ValueError) as error:
            raise GitCommandError("Git upstream counters were malformed.") from error

    def _raw_status(self) -> tuple[_RawStatusEntry, ...]:
        result = self._run_git(
            [
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--ignore-submodules=all",
            ]
        )
        if result.truncated:
            raise GitCommandError("Git status exceeds the configured output limit.")
        records = result.stdout.decode("utf-8", errors="replace").split("\0")
        entries: list[_RawStatusEntry] = []
        index = 0
        while index < len(records):
            record = records[index]
            index += 1
            if not record:
                continue
            if len(record) < 4 or record[2] != " ":
                raise GitCommandError("Git status output was malformed.")
            code = record[:2]
            path = record[3:]
            original_path = None
            if "R" in code or "C" in code:
                if index >= len(records) or not records[index]:
                    raise GitCommandError("Git rename status was malformed.")
                original_path = records[index]
                index += 1
            entries.append(
                _RawStatusEntry(
                    path=path,
                    index_status=code[0],
                    worktree_status=code[1],
                    original_path=original_path,
                )
            )
            if len(entries) > self.max_status_entries:
                raise GitCommandError("Git status exceeds the configured entry limit.")
        return tuple(entries)

    def _public_status(self, entry: _RawStatusEntry) -> GitFileStatus:
        sensitive = self._entry_is_sensitive(entry)
        return GitFileStatus(
            path=self._HIDDEN_PATH if sensitive else self._display_path(entry.path),
            index_status=entry.index_status,
            worktree_status=entry.worktree_status,
            original_path=(
                self._HIDDEN_PATH
                if sensitive and entry.original_path
                else self._display_path(entry.original_path)
                if entry.original_path
                else None
            ),
            sensitive=sensitive,
        )

    def _entry_is_sensitive(self, entry: _RawStatusEntry) -> bool:
        return self.guard.is_sensitive(entry.path) or bool(
            entry.original_path and self.guard.is_sensitive(entry.original_path)
        )

    @staticmethod
    def _is_untracked(entry: _RawStatusEntry) -> bool:
        return entry.index_status == "?" and entry.worktree_status == "?"

    def _paths_for(self, entries: list[_RawStatusEntry], *, staged: bool) -> list[str]:
        paths: set[str] = set()
        for entry in entries:
            if self._is_untracked(entry):
                continue
            status = entry.index_status if staged else entry.worktree_status
            if status == " ":
                continue
            paths.add(entry.path)
            if entry.original_path:
                paths.add(entry.original_path)
        return sorted(paths)

    def _untracked_diff(self, path: str) -> str:
        try:
            content = self.file_tool.read_file(path)
        except (FileAccessError, WorkspaceSecurityError):
            return f"Binary, oversized, or unsafe untracked file not shown: {path}\n"
        display_path = self._display_path(path)
        body = "".join(
            difflib.unified_diff(
                [],
                content.splitlines(keepends=True),
                fromfile="/dev/null",
                tofile=f"b/{display_path}",
            )
        )
        if not body:
            body = f"--- /dev/null\n+++ b/{display_path}\n"
        return f"diff --git a/{display_path} b/{display_path}\nnew file mode 100644\n{body}"

    @staticmethod
    def _display_path(path: str) -> str:
        return path.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")

    def _truncate_text(self, value: str) -> tuple[str, bool]:
        encoded = value.encode("utf-8")
        if len(encoded) <= self.max_output_bytes:
            return value, False
        return encoded[: self.max_output_bytes].decode("utf-8", errors="ignore"), True

    def _run_git(
        self,
        args: list[str],
        *,
        allowed_returncodes: tuple[int, ...] = (0,),
        mutating: bool = False,
        allow_truncation: bool = False,
    ) -> "_DecodedGitCommandResult":
        command = (
            str(self.git_executable),
            "--literal-pathspecs",
            "--no-pager",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(self.guard.root),
            *args,
        )
        stdout_capture = _BoundedBytes(self.max_output_bytes)
        stderr_capture = _BoundedBytes(65_536)
        started = monotonic()

        with tempfile.TemporaryDirectory(prefix="sagent-git-") as temp_home:
            environment = {
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_LITERAL_PATHSPECS": "1",
                "GIT_OPTIONAL_LOCKS": "1" if mutating else "0",
                "GIT_PAGER": "cat",
                "GIT_TERMINAL_PROMPT": "0",
                "HOME": temp_home,
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            }
            try:
                process = subprocess.Popen(  # noqa: S603 - exact internal Git argv.
                    command,
                    cwd=self.guard.root,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    close_fds=True,
                    start_new_session=True,
                )
            except OSError as error:
                raise GitCommandError("Git process could not be started.") from error
            if process.stdout is None or process.stderr is None:
                raise GitCommandError("Git output pipes were not created.")

            stdout_thread = Thread(target=stdout_capture.drain, args=(process.stdout,), daemon=True)
            stderr_thread = Thread(target=stderr_capture.drain, args=(process.stderr,), daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            try:
                returncode = process.wait(timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired as error:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise GitCommandError("Git command exceeded its timeout.") from error
            finally:
                stdout_thread.join(timeout=2)
                stderr_thread.join(timeout=2)

        result = _DecodedGitCommandResult(
            stdout=bytes(stdout_capture.data),
            stderr=bytes(stderr_capture.data),
            returncode=returncode,
            truncated=stdout_capture.truncated or stderr_capture.truncated,
            duration_ms=max(0, round((monotonic() - started) * 1_000)),
        )
        if result.returncode not in allowed_returncodes:
            detail = redact_secrets(result.stderr_text)[0].strip() or "Git command failed."
            raise GitCommandError(detail[:1_000])
        if result.truncated and not allow_truncation:
            raise GitCommandError("Git command output exceeded its configured limit.")
        return result


@dataclass(frozen=True, slots=True)
class _DecodedGitCommandResult:
    stdout: bytes
    stderr: bytes
    returncode: int
    truncated: bool
    duration_ms: int

    @property
    def stdout_text(self) -> str:
        return self.stdout.decode("utf-8", errors="replace")

    @property
    def stderr_text(self) -> str:
        return self.stderr.decode("utf-8", errors="replace")
