"""Allowlist-based process execution for bounded local test profiles."""

import math
import os
import re
import signal
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock, Thread
from time import monotonic
from types import MappingProxyType
from typing import BinaryIO
from uuid import UUID, uuid4

from sagent_tools.workspace import WorkspaceGuard


class TestProfileNotAllowedError(ValueError):
    """Raised when a caller requests a command outside the server allowlist."""


class TestCommandMismatchError(ValueError):
    """Raised when approval does not match the displayed command."""


class TestResultNotFoundError(KeyError):
    """Raised when a stored test result does not exist."""


class TestRunnerBusyError(RuntimeError):
    """Raised when another test profile is already running."""


class TestExecutionError(RuntimeError):
    """Raised when an allowlisted process cannot be started."""


@dataclass(frozen=True, slots=True)
class TestProfile:
    """A server-owned, exact process invocation exposed under a stable id."""

    profile_id: str
    command: str
    argv: tuple[str, ...]
    working_directory: str = "."
    timeout_seconds: float = 60.0


@dataclass(frozen=True, slots=True)
class TestProfileSummary:
    """Safe profile metadata shown before a human starts a test run."""

    profile_id: str
    command: str
    working_directory: str
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class TestResult:
    """Bounded, redacted output from one allowlisted test process."""

    result_id: UUID
    profile_id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    passed: bool
    created_at: datetime
    duration_ms: int
    timed_out: bool
    output_truncated: bool


class _BoundedCapture:
    """Drain one pipe fully while retaining only a fixed number of bytes."""

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._data = bytearray()
        self.truncated = False

    def drain(self, stream: BinaryIO) -> None:
        try:
            while chunk := stream.read(8_192):
                remaining = self._limit - len(self._data)
                if remaining > 0:
                    self._data.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    self.truncated = True
        finally:
            stream.close()

    def text(self) -> str:
        return self._data.decode("utf-8", errors="replace")


class TestRunner:
    """Run exact registered commands without accepting user-controlled argv."""

    _PROFILE_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
    _SECRET_PATTERNS = (
        re.compile(r"(?im)\b(api[_-]?key|password|secret|token)\s*[:=]\s*([^\s]+)"),
        re.compile(r"\b(?:gh[pousr]_|github_pat_|sk-)[A-Za-z0-9_\-]{16,}\b"),
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?"
            r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            re.DOTALL,
        ),
    )

    def __init__(
        self,
        guard: WorkspaceGuard,
        profiles: Iterable[TestProfile],
        *,
        max_output_bytes: int = 65_536,
        max_timeout_seconds: float = 300.0,
        max_results: int = 100,
    ) -> None:
        if max_output_bytes < 1 or max_timeout_seconds <= 0 or max_results < 1:
            raise ValueError("Test runner resource limits must be positive.")
        self.guard = guard
        self.max_output_bytes = max_output_bytes
        self.max_timeout_seconds = max_timeout_seconds
        self.max_results = max_results

        registered: dict[str, TestProfile] = {}
        for profile in profiles:
            self._validate_profile(profile)
            if profile.profile_id in registered:
                raise ValueError(f"Duplicate test profile: {profile.profile_id}")
            registered[profile.profile_id] = profile
        if not registered:
            raise ValueError("At least one allowlisted test profile is required.")

        self._profiles = MappingProxyType(registered)
        self._results: dict[UUID, TestResult] = {}
        self._results_lock = Lock()
        self._run_lock = Lock()

    def list_profiles(self) -> tuple[TestProfileSummary, ...]:
        """Expose commands for exact human review without leaking executable paths."""

        return tuple(
            TestProfileSummary(
                profile_id=profile.profile_id,
                command=profile.command,
                working_directory=profile.working_directory,
                timeout_seconds=profile.timeout_seconds,
            )
            for profile in self._profiles.values()
        )

    def run(self, profile_id: str, expected_command: str) -> TestResult:
        """Run one exact profile after matching the command shown to the user."""

        try:
            profile = self._profiles[profile_id]
        except KeyError as error:
            raise TestProfileNotAllowedError("Test profile is not allowlisted.") from error
        if profile.command != expected_command:
            raise TestCommandMismatchError(
                "Approved command does not match the registered test profile."
            )
        if not self._run_lock.acquire(blocking=False):
            raise TestRunnerBusyError("Another test profile is already running.")

        try:
            result = self._execute(profile)
            with self._results_lock:
                while len(self._results) >= self.max_results:
                    oldest_result_id = next(iter(self._results))
                    del self._results[oldest_result_id]
                self._results[result.result_id] = result
            return result
        finally:
            self._run_lock.release()

    def get(self, result_id: UUID) -> TestResult:
        """Return one immutable stored test result."""

        with self._results_lock:
            try:
                return self._results[result_id]
            except KeyError as error:
                raise TestResultNotFoundError(result_id) from error

    def _execute(self, profile: TestProfile) -> TestResult:
        started = monotonic()
        stdout_capture = _BoundedCapture(self.max_output_bytes)
        stderr_capture = _BoundedCapture(self.max_output_bytes)
        timed_out = False

        with tempfile.TemporaryDirectory(prefix="sagent-test-") as temp_home:
            wrapper = Path(__file__).with_name("_process_wrapper.py")
            wrapped_argv = (
                sys.executable,
                str(wrapper),
                str(max(1, math.ceil(profile.timeout_seconds) + 1)),
                *profile.argv,
            )
            try:
                process = subprocess.Popen(  # noqa: S603 - argv is server-owned and exact.
                    wrapped_argv,
                    cwd=self.guard.resolve(profile.working_directory, must_exist=True),
                    env=self._sanitized_environment(profile, Path(temp_home)),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    close_fds=True,
                    start_new_session=True,
                )
            except OSError as error:
                raise TestExecutionError(
                    "Allowlisted test process could not be started."
                ) from error

            if process.stdout is None or process.stderr is None:
                self._terminate_process_group(process)
                raise TestExecutionError("Test process output pipes were not created.")

            stdout_thread = Thread(
                target=stdout_capture.drain,
                args=(process.stdout,),
                daemon=True,
            )
            stderr_thread = Thread(
                target=stderr_capture.drain,
                args=(process.stderr,),
                daemon=True,
            )
            stdout_thread.start()
            stderr_thread.start()

            try:
                exit_code = process.wait(timeout=profile.timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                self._terminate_process_group(process)
                exit_code = process.wait()
            finally:
                stdout_thread.join(timeout=2)
                stderr_thread.join(timeout=2)

        duration_ms = max(0, round((monotonic() - started) * 1_000))
        stdout = self._redact(stdout_capture.text())
        stderr = self._redact(stderr_capture.text())
        output_truncated = stdout_capture.truncated or stderr_capture.truncated
        if stdout_capture.truncated:
            stdout = f"{stdout}\n[Sagent: Ausgabe gekürzt]"
        if stderr_capture.truncated:
            stderr = f"{stderr}\n[Sagent: Ausgabe gekürzt]"

        return TestResult(
            result_id=uuid4(),
            profile_id=profile.profile_id,
            command=profile.command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            passed=exit_code == 0 and not timed_out,
            created_at=datetime.now(UTC),
            duration_ms=duration_ms,
            timed_out=timed_out,
            output_truncated=output_truncated,
        )

    def _validate_profile(self, profile: TestProfile) -> None:
        if not self._PROFILE_ID.fullmatch(profile.profile_id):
            raise ValueError("Test profile id is invalid.")
        if not profile.command.strip() or len(profile.command) > 500:
            raise ValueError("Test profile display command is invalid.")
        if not profile.argv or any(not argument or "\x00" in argument for argument in profile.argv):
            raise ValueError("Test profile argv is invalid.")
        working_directory = self.guard.resolve(profile.working_directory, must_exist=True)
        if not working_directory.is_dir():
            raise ValueError("Test profile working directory must be a directory.")
        executable = Path(profile.argv[0])
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError("Test profile executable must be an existing absolute file.")
        if not os.access(executable, os.X_OK):
            raise ValueError("Test profile executable must be executable.")
        if not 0 < profile.timeout_seconds <= self.max_timeout_seconds:
            raise ValueError("Test profile timeout exceeds the configured limit.")

    def _sanitized_environment(self, profile: TestProfile, temp_home: Path) -> dict[str, str]:
        executable_directories = {
            str(Path(registered.argv[0]).parent) for registered in self._profiles.values()
        }
        executable_directories.add(str(Path(profile.argv[0]).parent))
        safe_system_paths = {"/usr/bin", "/bin", "/usr/sbin", "/sbin"}
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
            "PIP_NO_INDEX": "1",
            "PATH": os.pathsep.join(sorted(executable_directories | safe_system_paths)),
            "PNPM_CONFIG_OFFLINE": "true",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(temp_home / "pycache"),
            "PYTHONUNBUFFERED": "1",
            "TMPDIR": str(temp_home),
            "all_proxy": "http://127.0.0.1:9",
            "http_proxy": "http://127.0.0.1:9",
            "https_proxy": "http://127.0.0.1:9",
        }

    @staticmethod
    def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return

    @classmethod
    def _redact(cls, output: str) -> str:
        redacted = output
        redacted = cls._SECRET_PATTERNS[0].sub(
            lambda match: f"{match.group(1)}=[REDACTED]", redacted
        )
        redacted = cls._SECRET_PATTERNS[1].sub("[REDACTED]", redacted)
        return cls._SECRET_PATTERNS[2].sub("[REDACTED PRIVATE KEY]", redacted)
