"""CLI boundary tests for the opt-in benchmark harness."""

import json

import httpx2 as httpx

import sagent_agent_api.benchmark_cli as benchmark_cli
from sagent_agent_core import (
    BenchmarkObservation,
    BenchmarkReport,
    FakeModelAdapter,
    LoopbackEndpoint,
    LoopbackOpenAIChatAdapter,
    ModelCapability,
    ModelJobState,
    ModelRouter,
    ModelTransport,
)


def test_cli_without_confirmation_does_not_construct_router(capsys) -> None:
    def forbidden_builder() -> ModelRouter:
        raise AssertionError("Router must not be built without confirmation.")

    exit_code = benchmark_cli.main([], router_builder=forbidden_builder)
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["status"] == "blocked"
    assert output["error_code"] == "confirmation_required"
    assert "prompt" not in json.dumps(output)


def test_confirmed_cli_rejects_default_fake_only_router(capsys) -> None:
    fake = FakeModelAdapter()
    router = ModelRouter(
        [fake],
        {ModelCapability.CODING: fake.descriptor.adapter_id},
    )

    exit_code = benchmark_cli.main(["--confirmed"], router_builder=lambda: router)
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "benchmark_id": "sagent-local-model-v1",
        "error_code": "local_configuration_invalid",
        "status": "blocked",
    }


def test_successful_cli_serializes_metrics_only(monkeypatch, capsys) -> None:
    adapter = LoopbackOpenAIChatAdapter(
        LoopbackEndpoint("http://127.0.0.1:1234/v1"),
        "synthetic-local-model",
        adapter_id="local-lm-studio",
        provider="lm-studio",
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(
                AssertionError("CLI serialization test must not call a model adapter.")
            )
        ),
    )
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
        allowed_transports=frozenset({ModelTransport.LOOPBACK_HTTP}),
        allow_non_simulated=True,
    )

    class StubHarness:
        BENCHMARK_ID = "sagent-local-model-v1"

        def __init__(self, selected_router: ModelRouter, adapter_id: str) -> None:
            assert selected_router is router
            assert adapter_id == "local-lm-studio"

        def run(self, *, confirmed: bool) -> BenchmarkReport:
            assert confirmed is True
            return BenchmarkReport(
                benchmark_id=self.BENCHMARK_ID,
                adapter_id="local-lm-studio",
                observations=(
                    BenchmarkObservation(
                        task_id="synthetic-task",
                        status=ModelJobState.SUCCEEDED,
                        reachable=True,
                        latency_ms=1,
                        response_duration_ms=2,
                        total_duration_ms=3,
                        response_characters=12,
                        response_untrusted=True,
                        cancellation_requested=False,
                        cancellation_effective=False,
                        error_code=None,
                    ),
                ),
            )

    monkeypatch.setattr(benchmark_cli, "LocalModelBenchmarkHarness", StubHarness)

    exit_code = benchmark_cli.main(["--confirmed"], router_builder=lambda: router)
    output_text = capsys.readouterr().out
    output = json.loads(output_text)

    assert exit_code == 0
    assert output["status"] == "completed"
    assert output["observations"][0]["prompt_stored"] is False
    assert "prompt" not in output_text.replace('"prompt_stored"', "")
    assert "content" not in output_text
