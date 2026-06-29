"""Bounded in-memory lifecycle for cancellable local model requests."""

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from uuid import UUID, uuid4

from sagent_agent_core.model_runtime import (
    ModelCancellationToken,
    ModelCancelledError,
    ModelCapability,
    ModelContractError,
    ModelRequest,
    ModelResponse,
    ModelRouter,
    ModelRuntimeError,
    ModelTransport,
)


class ModelJobNotFoundError(KeyError):
    """Raised when a model job id is unknown or already evicted."""


class ModelJobConflictError(RuntimeError):
    """Raised when a terminal job cannot accept the requested transition."""


class ModelJobCapacityError(RuntimeError):
    """Raised when every bounded job slot is currently active."""


class ModelJobState(StrEnum):
    """Lifecycle states exposed by the cancellable job API."""

    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


_TERMINAL_STATES = frozenset(
    {ModelJobState.SUCCEEDED, ModelJobState.FAILED, ModelJobState.CANCELLED}
)


@dataclass(frozen=True, slots=True)
class ModelJobSnapshot:
    """Prompt-free immutable state safe to expose over the local API."""

    job_id: UUID
    adapter_id: str
    capability: ModelCapability
    state: ModelJobState
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    result: ModelResponse | None
    error: str | None


@dataclass(slots=True)
class _ModelJobRecord:
    job_id: UUID
    adapter_id: str
    capability: ModelCapability
    state: ModelJobState
    created_at: datetime
    request: ModelRequest | None
    cancellation: ModelCancellationToken
    future: Future[None] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: ModelResponse | None = None
    error: str | None = None


class ModelJobService:
    """Run a small number of local model calls with explicit cancellation."""

    def __init__(
        self,
        router: ModelRouter,
        *,
        max_workers: int = 1,
        max_jobs: int = 100,
    ) -> None:
        if max_workers < 1 or max_workers > 4 or max_jobs < 1 or max_jobs > 1_000:
            raise ValueError("Model job limits are outside the supported bounds.")
        self.router = router
        self.max_jobs = max_jobs
        self._jobs: dict[UUID, _ModelJobRecord] = {}
        self._lock = RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="sagent-model",
        )
        self._closed = False

    def submit(self, adapter_id: str, request: ModelRequest) -> ModelJobSnapshot:
        """Queue one prevalidated loopback request without retaining prompt in snapshots."""

        descriptor = next(
            (item for item in self.router.list_adapters() if item.adapter_id == adapter_id),
            None,
        )
        if descriptor is None:
            raise ModelContractError("Local model adapter is not configured.")
        if descriptor.transport is not ModelTransport.LOOPBACK_HTTP or descriptor.simulated:
            raise ModelContractError("Model jobs require a non-simulated loopback adapter.")

        with self._lock:
            if self._closed:
                raise ModelJobConflictError("Model job service is closed.")
            self._evict_terminal_jobs()
            if len(self._jobs) >= self.max_jobs:
                raise ModelJobCapacityError("All model job slots are active.")
            job_id = uuid4()
            record = _ModelJobRecord(
                job_id=job_id,
                adapter_id=adapter_id,
                capability=request.capability,
                state=ModelJobState.QUEUED,
                created_at=datetime.now(UTC),
                request=request,
                cancellation=ModelCancellationToken(),
            )
            self._jobs[job_id] = record
            future = self._executor.submit(self._run, job_id)
            record.future = future
            return self._snapshot(record)

    def get(self, job_id: UUID) -> ModelJobSnapshot:
        with self._lock:
            try:
                return self._snapshot(self._jobs[job_id])
            except KeyError as error:
                raise ModelJobNotFoundError(job_id) from error

    def cancel(self, job_id: UUID) -> ModelJobSnapshot:
        """Request cancellation once and return the latest observable state."""

        with self._lock:
            try:
                record = self._jobs[job_id]
            except KeyError as error:
                raise ModelJobNotFoundError(job_id) from error
            if record.state is ModelJobState.CANCELLED:
                return self._snapshot(record)
            if record.state in {ModelJobState.SUCCEEDED, ModelJobState.FAILED}:
                raise ModelJobConflictError("A completed model job cannot be cancelled.")
            record.state = ModelJobState.CANCELLING
            cancellation = record.cancellation
            future = record.future

        cancellation.cancel()
        future_cancelled = bool(future and future.cancel())
        if future_cancelled:
            with self._lock:
                record = self._jobs[job_id]
                self._mark_cancelled(record)
                return self._snapshot(record)
        return self.get(job_id)

    def close(self, *, wait: bool = True) -> None:
        """Cancel active jobs and release executor threads; idempotent for tests/shutdown."""

        with self._lock:
            if self._closed:
                return
            self._closed = True
            active = [
                record
                for record in self._jobs.values()
                if record.state not in _TERMINAL_STATES
            ]
        for record in active:
            record.cancellation.cancel()
        self._executor.shutdown(wait=wait, cancel_futures=True)
        with self._lock:
            for record in active:
                if record.state not in _TERMINAL_STATES:
                    self._mark_cancelled(record)

    def _run(self, job_id: UUID) -> None:
        with self._lock:
            record = self._jobs[job_id]
            if record.cancellation.is_cancelled or record.state is ModelJobState.CANCELLING:
                self._mark_cancelled(record)
                return
            request = record.request
            if request is None:
                record.state = ModelJobState.FAILED
                record.completed_at = datetime.now(UTC)
                record.error = "Model job request is unavailable."
                return
            record.state = ModelJobState.RUNNING
            record.started_at = datetime.now(UTC)

        try:
            response = self.router.complete(
                request,
                adapter_id=record.adapter_id,
                cancellation=record.cancellation,
            )
        except ModelCancelledError:
            with self._lock:
                self._mark_cancelled(record)
            return
        except (ModelContractError, ModelRuntimeError):
            with self._lock:
                if record.cancellation.is_cancelled:
                    self._mark_cancelled(record)
                else:
                    record.state = ModelJobState.FAILED
                    record.completed_at = datetime.now(UTC)
                    record.error = "Local model job failed safely."
                    record.request = None
            return
        except Exception:
            with self._lock:
                if record.cancellation.is_cancelled:
                    self._mark_cancelled(record)
                else:
                    record.state = ModelJobState.FAILED
                    record.completed_at = datetime.now(UTC)
                    record.error = "Local model job failed safely."
                    record.request = None
            return

        with self._lock:
            if record.cancellation.is_cancelled:
                self._mark_cancelled(record)
            else:
                record.state = ModelJobState.SUCCEEDED
                record.completed_at = datetime.now(UTC)
                record.result = response
                record.request = None

    def _evict_terminal_jobs(self) -> None:
        if len(self._jobs) < self.max_jobs:
            return
        terminal = sorted(
            (
                record
                for record in self._jobs.values()
                if record.state in _TERMINAL_STATES
            ),
            key=lambda record: record.completed_at or record.created_at,
        )
        while terminal and len(self._jobs) >= self.max_jobs:
            record = terminal.pop(0)
            del self._jobs[record.job_id]

    @staticmethod
    def _mark_cancelled(record: _ModelJobRecord) -> None:
        record.state = ModelJobState.CANCELLED
        record.completed_at = datetime.now(UTC)
        record.request = None
        record.result = None
        record.error = None

    @staticmethod
    def _snapshot(record: _ModelJobRecord) -> ModelJobSnapshot:
        return ModelJobSnapshot(
            job_id=record.job_id,
            adapter_id=record.adapter_id,
            capability=record.capability,
            state=record.state,
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            result=record.result,
            error=record.error,
        )
