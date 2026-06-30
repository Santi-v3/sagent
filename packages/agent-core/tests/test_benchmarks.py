"""Deterministic tests for the opt-in local-model benchmark harness."""

import json
from dataclasses import asdict
from threading import Event

import httpx2 as httpx
import pytest

from sagent_agent_core import (
    BenchmarkConfigurationError,
    BenchmarkConfirmationRequiredError,
    FakeModelAdapter,
    LocalModelBenchmarkHarness,
    LoopbackEndpoint,
    LoopbackOpenAIChatAdapter,
    ModelCapability,
    ModelJobState,
    ModelRouter,
    ModelTransport,
    SyntheticBenchmarkTask,
)

MODEL = "synthetic-local-model"


class BlockingJsonStream(httpx.SyncByteStream):
    def __init__(self, content: bytes) -> None:
        self.content = content
        self.started = Event()
        self.release = Event()
        self.closed = False

    def __iter__(self):
        midpoint = max(1, len(self.content) // 2)
        self.started.set()
        yield self.content[:midpoint]
        self.release.wait(2)
        if not self.closed:
            yield self.content[midpoint:]

    def close(self) -> None:
        self.closed = True
        self.release.set()


def payload(content: str = "Synthetic response only.") -> dict[str, object]:
    return {
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 4},
    }


def router_with_handler(
    handler,
    *,
    adapter_id: str = "local-lm-studio",
    provider: str = "lm-studio",
    port: int = 1_234,
) -> tuple[ModelRouter, str]:
    adapter = LoopbackOpenAIChatAdapter(
        LoopbackEndpoint(
            f"http://127.0.0.1:{port}/v1",
            allowed_ports=frozenset({port}),
        ),
        MODEL,
        adapter_id=adapter_id,
        provider=provider,
        transport=httpx.MockTransport(handler),
    )
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
        allowed_transports=frozenset({ModelTransport.LOOPBACK_HTTP}),
        allow_non_simulated=True,
    )
    return router, adapter.descriptor.adapter_id


def task(*, cancel: bool = False) -> SyntheticBenchmarkTask:
    return SyntheticBenchmarkTask(
        task_id="cancellation-probe" if cancel else "synthetic-task",
        capability=ModelCapability.CODING,
        prompt="Harmless synthetic prompt that must not appear in benchmark output.",
        cancel_after_start=cancel,
    )


def test_harness_blocks_without_confirmation_before_mock_request() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=payload())

    router, adapter_id = router_with_handler(handler)
    harness = LocalModelBenchmarkHarness(router, adapter_id, tasks=(task(),))

    with pytest.raises(BenchmarkConfirmationRequiredError, match="confirmation"):
        harness.run(confirmed=False)

    assert calls == 0


def test_success_report_contains_metrics_but_no_prompt_or_response_text() -> None:
    router, adapter_id = router_with_handler(
        lambda request: httpx.Response(200, json=payload("private model output"))
    )
    harness = LocalModelBenchmarkHarness(router, adapter_id, tasks=(task(),))

    report = harness.run(confirmed=True)
    observation = report.observations[0]
    serialized = json.dumps(asdict(report))

    assert observation.status is ModelJobState.SUCCEEDED
    assert observation.reachable is True
    assert observation.latency_ms is not None and observation.latency_ms >= 0
    assert observation.response_duration_ms is not None
    assert observation.response_characters == len("private model output")
    assert observation.response_untrusted is True
    assert observation.prompt_stored is False
    assert "Harmless synthetic prompt" not in serialized
    assert "private model output" not in serialized


def test_provider_failure_is_reduced_to_a_generic_error_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("provider-sensitive-timeout")

    router, adapter_id = router_with_handler(handler)
    harness = LocalModelBenchmarkHarness(router, adapter_id, tasks=(task(),))

    observation = harness.run(confirmed=True).observations[0]
    serialized = json.dumps(asdict(observation))

    assert observation.status is ModelJobState.FAILED
    assert observation.reachable is False
    assert observation.error_code == "local_model_job_failed"
    assert "provider-sensitive" not in serialized


def test_cancellation_probe_stops_before_or_during_response_and_records_no_content() -> None:
    stream = BlockingJsonStream(json.dumps(payload()).encode("utf-8"))
    router, adapter_id = router_with_handler(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            stream=stream,
        )
    )
    harness = LocalModelBenchmarkHarness(router, adapter_id, tasks=(task(cancel=True),))

    observation = harness.run(confirmed=True).observations[0]

    # RUNNING is published before the adapter opens its response stream. Both a
    # pre-dispatch cancellation and closing an already-started stream are safe.
    assert not stream.started.is_set() or stream.closed is True
    assert observation.status is ModelJobState.CANCELLED
    assert observation.cancellation_requested is True
    assert observation.cancellation_effective is True
    assert observation.response_characters is None
    assert observation.response_untrusted is None


def test_harness_rejects_fake_adapter_and_duplicate_task_ids() -> None:
    router, adapter_id = router_with_handler(
        lambda request: httpx.Response(200, json=payload())
    )
    duplicated = task()

    fake = FakeModelAdapter()
    fake_router = ModelRouter(
        [fake],
        {ModelCapability.CODING: fake.descriptor.adapter_id},
    )
    with pytest.raises(BenchmarkConfigurationError, match="loopback"):
        LocalModelBenchmarkHarness(fake_router, fake.descriptor.adapter_id, tasks=(task(),))

    with pytest.raises(BenchmarkConfigurationError, match="unique"):
        LocalModelBenchmarkHarness(
            router,
            adapter_id,
            tasks=(duplicated, duplicated),
        )


def test_harness_accepts_ollama_profile_and_rejects_custom_loopback_adapter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload())

    ollama_router, ollama_id = router_with_handler(
        handler,
        adapter_id="local-ollama",
        provider="ollama",
        port=11_434,
    )
    custom_router, custom_id = router_with_handler(
        handler,
        adapter_id="local-custom",
        provider="custom",
    )

    LocalModelBenchmarkHarness(ollama_router, ollama_id, tasks=(task(),))
    with pytest.raises(BenchmarkConfigurationError, match="loopback"):
        LocalModelBenchmarkHarness(custom_router, custom_id, tasks=(task(),))
