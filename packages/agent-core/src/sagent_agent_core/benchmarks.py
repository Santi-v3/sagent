"""Fixed, prompt-safe benchmark harness for explicitly enabled local models."""

import re
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from time import monotonic, sleep

from sagent_agent_core.model_jobs import (
    ModelJobConflictError,
    ModelJobNotFoundError,
    ModelJobService,
    ModelJobSnapshot,
    ModelJobState,
)
from sagent_agent_core.model_runtime import (
    ModelCapability,
    ModelInputPart,
    ModelInputSource,
    ModelRequest,
    ModelRouter,
    ModelTransport,
)


class BenchmarkError(RuntimeError):
    """Base class for benchmark failures safe to map to generic CLI errors."""


class BenchmarkConfirmationRequiredError(BenchmarkError):
    """Raised before dispatch when the human confirmation flag is absent."""


class BenchmarkConfigurationError(BenchmarkError):
    """Raised when the harness is not bound to one approved local adapter."""


class BenchmarkTimeoutError(BenchmarkError):
    """Raised after requesting cancellation for a job that exceeds the suite bound."""


_TASK_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_ALLOWED_ADAPTERS = {
    "local-lm-studio": "lm-studio",
    "local-ollama": "ollama",
}
_TERMINAL_STATES = frozenset(
    {ModelJobState.SUCCEEDED, ModelJobState.FAILED, ModelJobState.CANCELLED}
)


@dataclass(frozen=True, slots=True)
class SyntheticBenchmarkTask:
    """One fixed harmless prompt; prompt text is never copied into observations."""

    task_id: str
    capability: ModelCapability
    prompt: str = field(repr=False)
    max_output_tokens: int = 128
    cancel_after_start: bool = False

    def __post_init__(self) -> None:
        if not _TASK_ID.fullmatch(self.task_id):
            raise ValueError("Benchmark task id must be a bounded lowercase identifier.")
        if not self.prompt.strip() or len(self.prompt) > 2_000:
            raise ValueError("Synthetic benchmark prompt must be visible and bounded.")
        if (
            isinstance(self.max_output_tokens, bool)
            or not isinstance(self.max_output_tokens, int)
            or not 1 <= self.max_output_tokens <= 512
        ):
            raise ValueError("Benchmark output tokens must be between 1 and 512.")
        if not isinstance(self.cancel_after_start, bool):
            raise ValueError("Benchmark cancellation marker must be boolean.")


SYNTHETIC_BENCHMARK_TASKS = (
    SyntheticBenchmarkTask(
        task_id="safe-refactor-plan",
        capability=ModelCapability.CODING,
        prompt=(
            "Return exactly three concise steps for refactoring this synthetic pure "
            "function without changing behavior: def clamp(value, low, high): "
            "return max(low, min(value, high)). Do not use tools or external data."
        ),
    ),
    SyntheticBenchmarkTask(
        task_id="deterministic-test-cases",
        capability=ModelCapability.CODING,
        prompt=(
            "List exactly three deterministic unit-test cases for a synthetic add(a, b) "
            "function. Do not access files, tools, networks, or private data."
        ),
    ),
    SyntheticBenchmarkTask(
        task_id="cancellation-probe",
        capability=ModelCapability.CHAT,
        prompt=(
            "Generate a long numbered list of harmless placeholder words for a local "
            "cancellation test. Do not use tools, files, networks, or external data."
        ),
        max_output_tokens=512,
        cancel_after_start=True,
    ),
)


@dataclass(frozen=True, slots=True)
class BenchmarkObservation:
    """Metrics-only terminal observation without prompt or model response content."""

    task_id: str
    status: ModelJobState
    reachable: bool | None
    latency_ms: int | None
    response_duration_ms: int | None
    total_duration_ms: int
    response_characters: int | None
    response_untrusted: bool | None
    cancellation_requested: bool
    cancellation_effective: bool
    error_code: str | None
    prompt_stored: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """One bounded report suitable for stdout serialization only."""

    benchmark_id: str
    adapter_id: str
    observations: tuple[BenchmarkObservation, ...]


class LocalModelBenchmarkHarness:
    """Run fixed synthetic tasks through one configured non-remote loopback adapter."""

    BENCHMARK_ID = "sagent-local-model-v1"

    def __init__(
        self,
        router: ModelRouter,
        adapter_id: str,
        *,
        tasks: Sequence[SyntheticBenchmarkTask] = SYNTHETIC_BENCHMARK_TASKS,
        job_timeout_seconds: float = 180.0,
        poll_interval_seconds: float = 0.01,
    ) -> None:
        if not tasks or len(tasks) > 10:
            raise BenchmarkConfigurationError("Benchmark suite must contain 1 to 10 tasks.")
        task_ids = [task.task_id for task in tasks]
        if len(task_ids) != len(set(task_ids)):
            raise BenchmarkConfigurationError("Benchmark task ids must be unique.")
        if (
            isinstance(job_timeout_seconds, bool)
            or not isinstance(job_timeout_seconds, (int, float))
            or not 1 <= job_timeout_seconds <= 300
        ):
            raise BenchmarkConfigurationError("Benchmark timeout must be between 1s and 300s.")
        if (
            isinstance(poll_interval_seconds, bool)
            or not isinstance(poll_interval_seconds, (int, float))
            or not 0 < poll_interval_seconds <= 1
        ):
            raise BenchmarkConfigurationError("Benchmark poll interval is outside its bounds.")

        descriptor = next(
            (item for item in router.list_adapters() if item.adapter_id == adapter_id),
            None,
        )
        expected_provider = _ALLOWED_ADAPTERS.get(adapter_id)
        if (
            expected_provider is None
            or descriptor is None
            or descriptor.provider != expected_provider
            or descriptor.transport is not ModelTransport.LOOPBACK_HTTP
            or descriptor.simulated
        ):
            raise BenchmarkConfigurationError(
                "Benchmark requires one configured non-simulated loopback adapter."
            )

        self.router = router
        self.adapter_id = adapter_id
        self.tasks = tuple(tasks)
        self.job_timeout_seconds = job_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    def run(self, *, confirmed: bool) -> BenchmarkReport:
        """Run only after a literal human confirmation; never persist prompts or output."""

        if confirmed is not True:
            raise BenchmarkConfirmationRequiredError(
                "Local benchmark execution requires explicit confirmation."
            )

        jobs = ModelJobService(
            self.router,
            max_workers=1,
            max_jobs=len(self.tasks),
        )
        observations: list[BenchmarkObservation] = []
        try:
            for task in self.tasks:
                observations.append(self._run_task(jobs, task))
        finally:
            jobs.close(wait=True)
        return BenchmarkReport(
            benchmark_id=self.BENCHMARK_ID,
            adapter_id=self.adapter_id,
            observations=tuple(observations),
        )

    def _run_task(
        self,
        jobs: ModelJobService,
        task: SyntheticBenchmarkTask,
    ) -> BenchmarkObservation:
        request = ModelRequest(
            capability=task.capability,
            parts=(
                ModelInputPart(
                    ModelInputSource.POLICY,
                    "Return untrusted text only. Never call or authorize tools.",
                ),
                ModelInputPart(ModelInputSource.USER, task.prompt),
            ),
            max_output_tokens=task.max_output_tokens,
        )
        submitted = jobs.submit(self.adapter_id, request)
        deadline = monotonic() + self.job_timeout_seconds
        cancellation_requested = False

        while True:
            snapshot = jobs.get(submitted.job_id)
            if (
                task.cancel_after_start
                and not cancellation_requested
                and snapshot.state is ModelJobState.RUNNING
            ):
                snapshot = jobs.cancel(submitted.job_id)
                cancellation_requested = True
            if snapshot.state in _TERMINAL_STATES:
                return self._observation(
                    task.task_id,
                    snapshot,
                    cancellation_requested,
                )
            if monotonic() >= deadline:
                with suppress(ModelJobConflictError, ModelJobNotFoundError):
                    jobs.cancel(submitted.job_id)
                raise BenchmarkTimeoutError("Local benchmark job exceeded its time limit.")
            sleep(self.poll_interval_seconds)

    @staticmethod
    def _observation(
        task_id: str,
        snapshot: ModelJobSnapshot,
        cancellation_requested: bool,
    ) -> BenchmarkObservation:
        latency_ms = None
        if snapshot.started_at is not None:
            latency_ms = max(
                0,
                round((snapshot.started_at - snapshot.created_at).total_seconds() * 1_000),
            )
        response_duration_ms = None
        if snapshot.started_at is not None and snapshot.completed_at is not None:
            response_duration_ms = max(
                0,
                round((snapshot.completed_at - snapshot.started_at).total_seconds() * 1_000),
            )
        completed_at = snapshot.completed_at or snapshot.started_at or snapshot.created_at
        total_duration_ms = max(
            0,
            round((completed_at - snapshot.created_at).total_seconds() * 1_000),
        )
        result = snapshot.result
        return BenchmarkObservation(
            task_id=task_id,
            status=snapshot.state,
            reachable=(
                True
                if snapshot.state is ModelJobState.SUCCEEDED
                else False
                if snapshot.state is ModelJobState.FAILED
                else None
            ),
            latency_ms=latency_ms,
            response_duration_ms=response_duration_ms,
            total_duration_ms=total_duration_ms,
            response_characters=len(result.content) if result is not None else None,
            response_untrusted=result.untrusted if result is not None else None,
            cancellation_requested=cancellation_requested,
            cancellation_effective=(
                cancellation_requested and snapshot.state is ModelJobState.CANCELLED
            ),
            error_code=(
                "local_model_job_failed"
                if snapshot.state is ModelJobState.FAILED
                else None
            ),
        )
