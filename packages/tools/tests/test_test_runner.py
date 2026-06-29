"""Tests for bounded, allowlist-only test process execution."""

import sys
from pathlib import Path

import pytest

from sagent_tools import (
    TestCommandMismatchError as CommandMismatchError,
)
from sagent_tools import (
    TestProfile as RunnerProfile,
)
from sagent_tools import (
    TestProfileNotAllowedError as ProfileNotAllowedError,
)
from sagent_tools import TestResultNotFoundError as ResultNotFoundError
from sagent_tools import (
    TestRunner as Runner,
)
from sagent_tools import (
    WorkspaceGuard,
)


def profile(profile_id: str, script: str, *, timeout: float = 2) -> RunnerProfile:
    return RunnerProfile(
        profile_id=profile_id,
        command=f"python:{profile_id}",
        argv=(str(Path(sys.executable).resolve()), "-c", script),
        timeout_seconds=timeout,
    )


def test_successful_profile_is_stored(tmp_path: Path) -> None:
    runner = Runner(WorkspaceGuard(tmp_path), [profile("success", "print('ok')")])

    result = runner.run("success", "python:success")

    assert result.passed is True
    assert result.exit_code == 0
    assert result.stdout == "ok\n"
    assert result.stderr == ""
    assert result.created_at is not None
    assert runner.get(result.result_id) == result


def test_failed_profile_returns_structured_result(tmp_path: Path) -> None:
    runner = Runner(
        WorkspaceGuard(tmp_path),
        [profile("failure", "import sys; print('broken', file=sys.stderr); sys.exit(3)")],
    )

    result = runner.run("failure", "python:failure")

    assert result.passed is False
    assert result.exit_code == 3
    assert result.stderr == "broken\n"
    assert result.timed_out is False


def test_unknown_profile_and_changed_command_are_blocked(tmp_path: Path) -> None:
    runner = Runner(WorkspaceGuard(tmp_path), [profile("success", "print('ok')")])

    with pytest.raises(ProfileNotAllowedError, match="allowlisted"):
        runner.run("rm-everything", "rm -rf /")
    with pytest.raises(CommandMismatchError, match="does not match"):
        runner.run("success", "python:tampered")


def test_timeout_kills_process_and_is_recorded(tmp_path: Path) -> None:
    runner = Runner(
        WorkspaceGuard(tmp_path),
        [profile("timeout", "import time; time.sleep(5)", timeout=0.05)],
        max_timeout_seconds=1,
    )

    result = runner.run("timeout", "python:timeout")

    assert result.passed is False
    assert result.timed_out is True
    assert result.exit_code != 0
    assert result.duration_ms < 2_000


def test_output_is_bounded_and_secrets_are_redacted(tmp_path: Path) -> None:
    script = "print('token=super-secret-value'); print('x' * 200)"
    runner = Runner(
        WorkspaceGuard(tmp_path),
        [profile("bounded", script)],
        max_output_bytes=64,
    )

    result = runner.run("bounded", "python:bounded")

    assert result.output_truncated is True
    assert "super-secret-value" not in result.stdout
    assert "token=[REDACTED]" in result.stdout
    assert "Ausgabe gekürzt" in result.stdout


def test_profiles_require_existing_absolute_executable(tmp_path: Path) -> None:
    invalid = RunnerProfile(
        profile_id="invalid",
        command="pytest",
        argv=("pytest",),
    )

    with pytest.raises(ValueError, match="absolute"):
        Runner(WorkspaceGuard(tmp_path), [invalid])


def test_result_history_is_bounded(tmp_path: Path) -> None:
    runner = Runner(
        WorkspaceGuard(tmp_path),
        [profile("success", "print('ok')")],
        max_results=1,
    )

    first = runner.run("success", "python:success")
    second = runner.run("success", "python:success")

    with pytest.raises(ResultNotFoundError):
        runner.get(first.result_id)
    assert runner.get(second.result_id) == second
