"""Tests for the provider-neutral, offline-only model runtime."""

from dataclasses import dataclass
from uuid import uuid4

import pytest

from sagent_agent_core import (
    FakeModelAdapter,
    ModelAdapterBlockedError,
    ModelAdapterDescriptor,
    ModelAdapterExecutionError,
    ModelCancellationToken,
    ModelCancelledError,
    ModelCapability,
    ModelContractError,
    ModelFinishReason,
    ModelInputPart,
    ModelInputSource,
    ModelRequest,
    ModelResponse,
    ModelResponseError,
    ModelRouteNotFoundError,
    ModelRouter,
    ModelTransport,
    ModelTransportBlockedError,
    ModelUsage,
)


def request(
    content: str = "Plane eine kleine Änderung.",
    *,
    capability: ModelCapability = ModelCapability.CODING,
) -> ModelRequest:
    return ModelRequest(
        capability=capability,
        parts=(ModelInputPart(source=ModelInputSource.USER, content=content),),
        max_output_tokens=128,
    )


@dataclass
class StaticAdapter:
    descriptor: ModelAdapterDescriptor
    content: str = "static response"
    wrong_request_id: bool = False
    fail: bool = False
    call_count: int = 0

    def complete(
        self,
        model_request: ModelRequest,
        *,
        cancellation: ModelCancellationToken | None = None,
    ) -> ModelResponse:
        self.call_count += 1
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        if self.fail:
            raise RuntimeError("provider detail that must not escape")
        return ModelResponse(
            request_id=uuid4() if self.wrong_request_id else model_request.request_id,
            adapter_id=self.descriptor.adapter_id,
            model=self.descriptor.model,
            content=self.content,
            finish_reason=ModelFinishReason.STOP,
            usage=ModelUsage(input_tokens=1, output_tokens=1),
        )


def descriptor(
    adapter_id: str,
    *,
    transport: ModelTransport = ModelTransport.IN_PROCESS,
    capabilities: frozenset[ModelCapability] | None = None,
    simulated: bool = True,
) -> ModelAdapterDescriptor:
    return ModelAdapterDescriptor(
        adapter_id=adapter_id,
        provider="tests",
        model=f"{adapter_id}-model",
        capabilities=capabilities or frozenset({ModelCapability.CODING}),
        transport=transport,
        simulated=simulated,
    )


def test_fake_adapter_is_deterministic_offline_and_untrusted() -> None:
    adapter = FakeModelAdapter()
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
    )
    first_request = request()
    second_request = request()

    first = router.complete(first_request)
    second = router.complete(second_request)

    assert first.content == second.content
    assert first.request_id == first_request.request_id
    assert first.untrusted is True
    assert first.adapter_id == "offline-fake"
    assert "keinen Modell-, Netzwerk- oder Tool-Aufruf" in first.content
    assert not hasattr(first, "tool_calls")
    assert router.list_adapters()[0].transport is ModelTransport.IN_PROCESS


def test_router_uses_explicit_capability_routes() -> None:
    chat = StaticAdapter(
        descriptor(
            "chat-fake",
            capabilities=frozenset({ModelCapability.CHAT}),
        )
    )
    coding = StaticAdapter(descriptor("coding-fake"))
    router = ModelRouter(
        [coding, chat],
        {
            ModelCapability.CHAT: "chat-fake",
            ModelCapability.CODING: "coding-fake",
        },
    )

    response = router.complete(request(capability=ModelCapability.CHAT))

    assert response.adapter_id == "chat-fake"
    assert chat.call_count == 1
    assert coding.call_count == 0


def test_router_blocks_loopback_and_remote_transports_before_execution() -> None:
    loopback = StaticAdapter(
        descriptor("lm-studio", transport=ModelTransport.LOOPBACK_HTTP)
    )
    router = ModelRouter([loopback], {ModelCapability.CODING: "lm-studio"})

    with pytest.raises(ModelTransportBlockedError, match="loopback_http"):
        router.complete(request())

    assert loopback.call_count == 0


def test_router_blocks_non_simulated_adapters_before_execution() -> None:
    real_adapter = StaticAdapter(descriptor("real-adapter", simulated=False))
    router = ModelRouter([real_adapter], {ModelCapability.CODING: "real-adapter"})

    with pytest.raises(ModelAdapterBlockedError, match="explicit runtime enablement"):
        router.complete(request())

    assert real_adapter.call_count == 0


def test_router_enforces_input_part_and_character_limits() -> None:
    adapter = FakeModelAdapter()
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
        max_parts=1,
        max_input_characters=8,
    )
    too_many_parts = ModelRequest(
        capability=ModelCapability.CODING,
        parts=(
            ModelInputPart(ModelInputSource.USER, "one"),
            ModelInputPart(ModelInputSource.WORKSPACE, "two"),
        ),
    )

    with pytest.raises(ModelContractError, match="part limit"):
        router.complete(too_many_parts)
    with pytest.raises(ModelContractError, match="input limit"):
        router.complete(request("nine chars"))


def test_router_rejects_oversized_or_mismatched_responses() -> None:
    oversized = StaticAdapter(descriptor("oversized"), content="x" * 20)
    router = ModelRouter(
        [oversized],
        {ModelCapability.CODING: "oversized"},
        max_output_characters=10,
    )

    with pytest.raises(ModelResponseError, match="output limit"):
        router.complete(request())

    mismatched = StaticAdapter(descriptor("mismatched"), wrong_request_id=True)
    mismatch_router = ModelRouter(
        [mismatched],
        {ModelCapability.CODING: "mismatched"},
    )
    with pytest.raises(ModelResponseError, match="does not match"):
        mismatch_router.complete(request())


def test_adapter_failures_are_wrapped_without_provider_details() -> None:
    failing = StaticAdapter(descriptor("failing"), fail=True)
    router = ModelRouter([failing], {ModelCapability.CODING: "failing"})

    with pytest.raises(ModelAdapterExecutionError, match="execution failed") as captured:
        router.complete(request())

    assert "provider detail" not in str(captured.value)


def test_missing_routes_and_unknown_explicit_adapters_are_rejected() -> None:
    adapter = FakeModelAdapter(capabilities=frozenset({ModelCapability.CHAT}))
    router = ModelRouter([adapter], {ModelCapability.CHAT: adapter.descriptor.adapter_id})

    with pytest.raises(ModelRouteNotFoundError, match="coding"):
        router.complete(request())
    with pytest.raises(ModelRouteNotFoundError, match="not registered"):
        router.complete(
            request(capability=ModelCapability.CHAT),
            adapter_id="missing",
        )


def test_invalid_descriptors_routes_and_streaming_are_rejected() -> None:
    with pytest.raises(ModelContractError, match="adapter_id"):
        descriptor("Invalid Adapter")

    adapter = FakeModelAdapter(capabilities=frozenset({ModelCapability.CHAT}))
    with pytest.raises(ModelContractError, match="unsupported capability"):
        ModelRouter([adapter], {ModelCapability.CODING: adapter.descriptor.adapter_id})

    streaming_request = ModelRequest(
        capability=ModelCapability.CHAT,
        parts=(ModelInputPart(ModelInputSource.USER, "hello"),),
        stream=True,
    )
    router = ModelRouter([adapter], {ModelCapability.CHAT: adapter.descriptor.adapter_id})
    with pytest.raises(ModelContractError, match="streaming"):
        router.complete(streaming_request)


def test_cancellation_token_is_thread_safe_idempotent_and_closes_resources() -> None:
    token = ModelCancellationToken()
    calls: list[str] = []
    unregister = token.add_cancel_callback(lambda: calls.append("registered"))

    assert token.cancel() is True
    assert token.cancel() is False
    unregister()
    token.add_cancel_callback(lambda: calls.append("late"))

    assert token.is_cancelled is True
    assert token.wait(0) is True
    assert calls == ["registered", "late"]
    with pytest.raises(ModelCancelledError, match="cancelled"):
        token.raise_if_cancelled()


def test_router_blocks_a_precancelled_request_before_adapter_execution() -> None:
    adapter = FakeModelAdapter()
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
    )
    token = ModelCancellationToken()
    token.cancel()

    with pytest.raises(ModelCancelledError, match="cancelled"):
        router.complete(request(), cancellation=token)
