"""Approval-gated test-runner contract with capability-policy gating.

Every test run goes through three phases:
  1. Preview — returns metadata + approval_hash (no execution)
  2. Approve — stores approval (no execution)
  3. Run — executes only if approved + hash matches

All commands come from a fixed allowlist — no free-form strings,
no shell=True, no git, no network, no cloud, no model calls.
"""

import hashlib
import os
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final
from uuid import UUID, uuid4

from sagent_agent_core import (
    DEFAULT_CAPABILITY_POLICY,
    CapabilityDecision,
    CapabilityName,
    evaluate_capability,
)


class TestCommandNotAllowedError(ValueError):
    """Raised when a caller requests a command outside the fixed allowlist."""
    __test__ = False


class TestRunNotFoundError(KeyError):
    """Raised when a test-run id does not exist."""
    __test__ = False


class TestRunHashMismatchError(ValueError):
    """Raised when the approval hash does not match the previewed hash."""
    __test__ = False


class TestRunNotApprovedError(RuntimeError):
    """Raised when a test run is attempted without prior approval."""
    __test__ = False


class TestRunConflictError(RuntimeError):
    """Raised when a test run is already in progress or has been used."""
    __test__ = False


class RunnerExecutionError(RuntimeError):
    """Raised when the allowlisted process cannot be started."""
    __test__ = False


@dataclass(frozen=True, slots=True)
class TestCommand:
    """One allowlisted test command — argv is fixed, never user-supplied."""

    command_id: str
    display_name: str
    argv: tuple[str, ...]
    timeout_seconds: float = 60.0


@dataclass(slots=True)
class TestRunState:
    """Mutable state for one test run through preview → approve → run."""

    test_run_id: UUID
    command_id: str
    approval_hash: str
    approved: bool = False
    completed: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    output_truncated: bool = False
    error: str | None = None


FIXED_TEST_COMMANDS: Final[dict[str, TestCommand]] = {
    "python-pytest-all": TestCommand(
        command_id="python-pytest-all",
        display_name="Python: all project tests",
        argv=(sys.executable, "-m", "pytest", "-q"),
        timeout_seconds=120.0,
    ),
    "python-pytest-capability": TestCommand(
        command_id="python-pytest-capability",
        display_name="Python: capability policy tests",
        argv=(sys.executable, "-m", "pytest", "-q",
              "packages/agent-core/tests/test_capability_policy.py"),
        timeout_seconds=60.0,
    ),
    "python-pytest-preview": TestCommand(
        command_id="python-pytest-preview",
        display_name="Python: capability preview tests",
        argv=(sys.executable, "-m", "pytest", "-q",
              "apps/agent-api/tests/test_capability_preview.py"),
        timeout_seconds=60.0,
    ),
    "python-lint": TestCommand(
        command_id="python-lint",
        display_name="Python: Ruff lint",
        argv=(sys.executable, "-m", "ruff", "check", "apps/agent-api", "packages"),
        timeout_seconds=60.0,
    ),
}

_TEST_RUNS: dict[UUID, TestRunState] = {}
_TEST_RUNS_LOCK = threading.Lock()
_RUN_EXECUTION_LOCK = threading.Lock()
_RUN_WORKSPACE_ROOT: Path | None = None

_APPROVAL_TOKEN: Final[str] = os.urandom(32).hex()


def _get_workspace_root() -> Path:
    root = _RUN_WORKSPACE_ROOT
    if root is not None:
        return root
    return Path(__file__).resolve().parents[4]


def configure_workspace_root(path: str | Path) -> None:
    global _RUN_WORKSPACE_ROOT
    _RUN_WORKSPACE_ROOT = Path(path).resolve()


def list_test_commands() -> list[TestCommand]:
    return list(FIXED_TEST_COMMANDS.values())


def get_test_command(command_id: str) -> TestCommand:
    cmd = FIXED_TEST_COMMANDS.get(command_id)
    if cmd is None:
        raise TestCommandNotAllowedError(
            f"Unknown test command: {command_id}"
        )
    return cmd


def _compute_approval_hash(test_run_id: UUID, command_id: str) -> str:
    return hashlib.sha256(
        f"{test_run_id}:{command_id}:{_APPROVAL_TOKEN}".encode()
    ).hexdigest()


def preview_test_run(command_id: str) -> tuple[TestRunState, CapabilityDecision]:
    get_test_command(command_id)

    decision = evaluate_capability(
        DEFAULT_CAPABILITY_POLICY,
        CapabilityName.RUN_TESTS,
    )

    test_run_id = uuid4()
    approval_hash = _compute_approval_hash(test_run_id, command_id)

    state = TestRunState(
        test_run_id=test_run_id,
        command_id=command_id,
        approval_hash=approval_hash,
    )

    with _TEST_RUNS_LOCK:
        _TEST_RUNS[test_run_id] = state

    return state, decision


def approve_test_run(test_run_id: UUID, approval_hash: str) -> TestRunState:
    with _TEST_RUNS_LOCK:
        state = _TEST_RUNS.get(test_run_id)
        if state is None:
            raise TestRunNotFoundError(f"Test run not found: {test_run_id}")
        if state.approved:
            raise TestRunConflictError("Test run is already approved.")
        if state.completed:
            raise TestRunConflictError("Test run is already completed.")
        if state.approval_hash != approval_hash:
            raise TestRunHashMismatchError("Approval hash does not match.")

        state.approved = True

    return state


def execute_test_run(
    test_run_id: UUID,
    approval_hash: str,
    confirmed: bool,
) -> TestRunState:
    if not confirmed:
        raise TestRunConflictError("Test run must be explicitly confirmed.")

    with _TEST_RUNS_LOCK:
        state = _TEST_RUNS.get(test_run_id)
        if state is None:
            raise TestRunNotFoundError(f"Test run not found: {test_run_id}")
        if not state.approved:
            raise TestRunNotApprovedError(
                "Test run must be approved before execution."
            )
        if state.completed:
            raise TestRunConflictError("Test run is already completed.")
        if state.approval_hash != approval_hash:
            raise TestRunHashMismatchError("Approval hash does not match.")

        state.completed = True
        state.started_at = datetime.now(UTC)

    if not _RUN_EXECUTION_LOCK.acquire(blocking=False):
        with _TEST_RUNS_LOCK:
            state.completed = False
            state.error = "Another test run is already executing."
        raise TestRunConflictError("Another test run is already executing.")

    try:
        cmd = get_test_command(state.command_id)
        _run_process(state, cmd)
    finally:
        _RUN_EXECUTION_LOCK.release()

    return state


def _run_process(state: TestRunState, cmd: TestCommand) -> None:
    stdout_limit = 20_480
    stderr_limit = 20_480
    timed_out = False

    with tempfile.TemporaryDirectory(prefix="sagent-test-runner-") as temp_home:
        temp_path = Path(temp_home)
        env = _sanitized_environment(temp_path)

        try:
            process = subprocess.Popen(  # noqa: S603 — argv from fixed allowlist, not user input
                cmd.argv,
                cwd=_get_workspace_root(),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                close_fds=True,
                start_new_session=True,
            )
        except OSError as error:
            state.error = "Test process could not be started."
            state.completed_at = datetime.now(UTC)
            raise RunnerExecutionError(
                "Allowlisted test process could not be started."
            ) from error

        if process.stdout is None or process.stderr is None:
            _terminate_process_group(process)
            state.error = "Test process output pipes were not created."
            state.completed_at = datetime.now(UTC)
            raise RunnerExecutionError("Test process output pipes were not created.")

        stdout_data = _capture_output(process.stdout, stdout_limit)
        stderr_data = _capture_output(process.stderr, stderr_limit)

        try:
            exit_code = process.wait(timeout=cmd.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_group(process)
            exit_code = process.wait()

        stdout_text, stdout_truncated = stdout_data
        stderr_text, stderr_truncated = stderr_data

        state.exit_code = exit_code
        state.stdout = stdout_text
        state.stderr = stderr_text
        state.timed_out = timed_out
        state.output_truncated = stdout_truncated or stderr_truncated
        state.completed_at = datetime.now(UTC)


def _sanitized_environment(temp_home: Path) -> dict[str, str]:
    return {
        "CI": "1",
        "ALL_PROXY": "http://127.0.0.1:9",
        "HOME": str(temp_home),
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "NO_COLOR": "1",
        "NO_PROXY": "",
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPYCACHEPREFIX": str(temp_home / "pycache"),
        "PYTHONUNBUFFERED": "1",
        "TMPDIR": str(temp_home),
        "all_proxy": "http://127.0.0.1:9",
        "http_proxy": "http://127.0.0.1:9",
        "https_proxy": "http://127.0.0.1:9",
    }


def _capture_output(
    stream: subprocess.PIPE, limit: int
) -> tuple[str, bool]:
    data = bytearray()
    truncated = False
    try:
        while chunk := stream.read(8_192):
            remaining = limit - len(data)
            if remaining > 0:
                data.extend(chunk[:remaining])
            if len(chunk) > remaining:
                truncated = True
    finally:
        stream.close()
    return data.decode("utf-8", errors="replace"), truncated


def _terminate_process_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def get_test_run(test_run_id: UUID) -> TestRunState:
    with _TEST_RUNS_LOCK:
        state = _TEST_RUNS.get(test_run_id)
        if state is None:
            raise TestRunNotFoundError(f"Test run not found: {test_run_id}")
        return state


def reset() -> None:
    with _TEST_RUNS_LOCK:
        _TEST_RUNS.clear()
    global _RUN_WORKSPACE_ROOT
    _RUN_WORKSPACE_ROOT = None
