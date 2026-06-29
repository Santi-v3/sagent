"""Concurrency and lifecycle tests for cancellable model jobs."""

from threading import Event
from time import monotonic, sleep

import pytest

from sagent_agent_core import (
    ModelAdapterDescriptor,
    ModelCancellationToken,
    ModelCancelledError,
    ModelCapability,
    ModelFinishReason,
    ModelInputPart,
    ModelInputSource,
    ModelJobCapacityError,
    ModelJobConflictError,
    ModelJobNotFoundError,
    ModelJobService,
    ModelJobState,
    ModelRequest,
    ModelResponse,
    ModelRouter,
    ModelTransport,
    ModelUsage,
)


class JobAdapter:
    descriptor = ModelAdapterDescriptor(
        adapter_id="local-job-test",
        provider="tests",
        model="test-model",
        capabilities=frozenset({ModelCapability.CHAT}),
        transport=ModelTransport.LOOPBACK_HTTP,
        simulated=False,
    )

    def __init__(self, *, block: bool = False, fail: bool = False) -> None:
        self.block = block
        self.fail = fail
        self.started = Event()

    def complete(
        self,
        request: ModelRequest,
        *,
        cancellation: ModelCancellationToken | None = None,
    ) -> ModelResponse:
        self.started.set()
        if self.block:
            assert cancellation is not None
            cancellation.wait(2)
            cancellation.raise_if_cancelled()
        if self.fail:
            raise RuntimeError("provider-sensitive-job-detail")
        return ModelResponse(
            request_id=request.request_id,
            adapter_id=self.descriptor.adapter_id,
            model=self.descriptor.model,
            content="safe result",
            finish_reason=ModelFinishReason.STOP,
            usage=ModelUsage(input_tokens=2, output_tokens=2),
        )


def request() -> ModelRequest:
    return ModelRequest(
        capability=ModelCapability.CHAT,
        parts=(ModelInputPart(ModelInputSource.USER, "private prompt is not exposed"),),
    )


def service(adapter: JobAdapter, *, max_jobs: int = 100) -> ModelJobService:
    router = ModelRouter(
        [adapter],
        {ModelCapability.CHAT: adapter.descriptor.adapter_id},
        allowed_transports=frozenset({ModelTransport.LOOPBACK_HTTP}),
        allow_non_simulated=True,
    )
    return ModelJobService(router, max_workers=1, max_jobs=max_jobs)


def wait_for_terminal(job_service: ModelJobService, job_id, timeout: float = 2):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        snapshot = job_service.get(job_id)
        if snapshot.state in {
            ModelJobState.SUCCEEDED,
            ModelJobState.FAILED,
            ModelJobState.CANCELLED,
        }:
            return snapshot
        sleep(0.01)
    raise AssertionError("Model job did not reach a terminal state.")


def test_successful_job_returns_prompt_free_immutable_result() -> None:
    adapter = JobAdapter()
    job_service = service(adapter)
    try:
        submitted = job_service.submit(adapter.descriptor.adapter_id, request())
        completed = wait_for_terminal(job_service, submitted.job_id)

        assert submitted.state in {ModelJobState.QUEUED, ModelJobState.RUNNING}
        assert completed.state is ModelJobState.SUCCEEDED
        assert completed.result is not None
        assert completed.result.content == "safe result"
        assert completed.started_at is not None
        assert completed.completed_at is not None
        assert not hasattr(completed, "request")
        assert not hasattr(completed, "prompt")
    finally:
        job_service.close()


def test_running_job_can_be_cancelled_idempotently() -> None:
    adapter = JobAdapter(block=True)
    job_service = service(adapter)
    try:
        submitted = job_service.submit(adapter.descriptor.adapter_id, request())
        assert adapter.started.wait(1)

        cancelling = job_service.cancel(submitted.job_id)
        completed = wait_for_terminal(job_service, submitted.job_id)
        repeated = job_service.cancel(submitted.job_id)

        assert cancelling.state in {ModelJobState.CANCELLING, ModelJobState.CANCELLED}
        assert completed.state is ModelJobState.CANCELLED
        assert repeated.state is ModelJobState.CANCELLED
        assert completed.result is None
        assert completed.error is None
    finally:
        job_service.close()


def test_queued_job_is_cancelled_without_execution() -> None:
    adapter = JobAdapter(block=True)
    job_service = service(adapter)
    try:
        running = job_service.submit(adapter.descriptor.adapter_id, request())
        assert adapter.started.wait(1)
        queued = job_service.submit(adapter.descriptor.adapter_id, request())

        cancelled = job_service.cancel(queued.job_id)

        assert cancelled.state is ModelJobState.CANCELLED
        job_service.cancel(running.job_id)
        assert wait_for_terminal(job_service, running.job_id).state is ModelJobState.CANCELLED
    finally:
        job_service.close()


def test_job_failures_are_generic_and_terminal_jobs_cannot_be_cancelled() -> None:
    adapter = JobAdapter(fail=True)
    job_service = service(adapter)
    try:
        submitted = job_service.submit(adapter.descriptor.adapter_id, request())
        failed = wait_for_terminal(job_service, submitted.job_id)

        assert failed.state is ModelJobState.FAILED
        assert failed.error == "Local model job failed safely."
        assert "provider" not in failed.error
        with pytest.raises(ModelJobConflictError, match="completed"):
            job_service.cancel(submitted.job_id)
    finally:
        job_service.close()


def test_capacity_blocks_active_overflow_and_evicts_old_terminal_jobs() -> None:
    blocking_adapter = JobAdapter(block=True)
    blocking_service = service(blocking_adapter, max_jobs=1)
    try:
        active = blocking_service.submit(blocking_adapter.descriptor.adapter_id, request())
        assert blocking_adapter.started.wait(1)
        with pytest.raises(ModelJobCapacityError, match="slots"):
            blocking_service.submit(blocking_adapter.descriptor.adapter_id, request())
        blocking_service.cancel(active.job_id)
        wait_for_terminal(blocking_service, active.job_id)
    finally:
        blocking_service.close()

    quick_adapter = JobAdapter()
    quick_service = service(quick_adapter, max_jobs=1)
    try:
        first = quick_service.submit(quick_adapter.descriptor.adapter_id, request())
        wait_for_terminal(quick_service, first.job_id)
        second = quick_service.submit(quick_adapter.descriptor.adapter_id, request())

        with pytest.raises(ModelJobNotFoundError):
            quick_service.get(first.job_id)
        assert wait_for_terminal(quick_service, second.job_id).state is ModelJobState.SUCCEEDED
    finally:
        quick_service.close()


def test_precancelled_adapter_signal_is_a_cancelled_job_not_failure() -> None:
    class SelfCancellingAdapter(JobAdapter):
        def complete(
            self,
            model_request: ModelRequest,
            *,
            cancellation: ModelCancellationToken | None = None,
        ) -> ModelResponse:
            assert cancellation is not None
            cancellation.cancel()
            raise ModelCancelledError("cancelled internally")

    adapter = SelfCancellingAdapter()
    job_service = service(adapter)
    try:
        submitted = job_service.submit(adapter.descriptor.adapter_id, request())
        completed = wait_for_terminal(job_service, submitted.job_id)

        assert completed.state is ModelJobState.CANCELLED
    finally:
        job_service.close()
