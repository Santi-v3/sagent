"""Provider-neutral model contracts with an offline-only deterministic router."""

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4


class ModelRuntimeError(RuntimeError):
    """Base class for bounded model-runtime failures."""


class ModelContractError(ValueError):
    """Raised when a request, descriptor, or route violates the model contract."""


class ModelRouteNotFoundError(ModelRuntimeError):
    """Raised when no adapter is configured for a requested capability."""


class ModelTransportBlockedError(ModelRuntimeError):
    """Raised when an adapter transport is outside the explicit allowlist."""


class ModelAdapterBlockedError(ModelRuntimeError):
    """Raised when a non-simulated adapter has not been explicitly enabled."""


class ModelAdapterExecutionError(ModelRuntimeError):
    """Raised when an adapter fails without exposing provider internals."""


class ModelResponseError(ModelRuntimeError):
    """Raised when an adapter returns an invalid or oversized response."""


class ModelCapability(StrEnum):
    """Capabilities that can be routed independently later."""

    CHAT = "chat"
    CODING = "coding"


class ModelInputSource(StrEnum):
    """Provenance labels preserved across the model boundary."""

    POLICY = "policy"
    USER = "user"
    WORKSPACE = "workspace"
    MEMORY = "memory"
    TOOL_RESULT = "tool_result"


class ModelTransport(StrEnum):
    """Transport classes used as an enforceable router boundary."""

    IN_PROCESS = "in_process"
    LOOPBACK_HTTP = "loopback_http"
    REMOTE_HTTP = "remote_http"


class ModelFinishReason(StrEnum):
    """Small provider-neutral completion state."""

    STOP = "stop"
    LENGTH = "length"


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")


def _validate_label(value: str, field_name: str, *, max_length: int = 128) -> None:
    if not value or len(value) > max_length or any(character in value for character in "\r\n\0"):
        raise ModelContractError(f"{field_name} must be a bounded single-line value.")


@dataclass(frozen=True, slots=True)
class ModelInputPart:
    """One source-labelled text part; labels do not grant tool authority."""

    source: ModelInputSource
    content: str

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ModelContractError("Model input parts must contain visible text.")


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """One immutable request accepted by any compatible adapter."""

    capability: ModelCapability
    parts: tuple[ModelInputPart, ...]
    max_output_tokens: int = 512
    temperature: float = 0.0
    stream: bool = False
    request_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not self.parts:
            raise ModelContractError("A model request requires at least one input part.")
        if not 1 <= self.max_output_tokens <= 8_192:
            raise ModelContractError("max_output_tokens must be between 1 and 8192.")
        if not 0.0 <= self.temperature <= 2.0:
            raise ModelContractError("temperature must be between 0 and 2.")


@dataclass(frozen=True, slots=True)
class ModelUsage:
    """Provider-reported or estimated token usage without billing data."""

    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ModelContractError("Model usage cannot be negative.")


@dataclass(frozen=True, slots=True)
class ModelAdapterDescriptor:
    """Reviewable metadata used by the router before adapter execution."""

    adapter_id: str
    provider: str
    model: str
    capabilities: frozenset[ModelCapability]
    transport: ModelTransport
    simulated: bool
    supports_streaming: bool = False

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.adapter_id):
            raise ModelContractError("adapter_id must be a stable lowercase identifier.")
        _validate_label(self.provider, "provider")
        _validate_label(self.model, "model")
        if not self.capabilities:
            raise ModelContractError("An adapter must declare at least one capability.")


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Text returned by an adapter; content is always untrusted data."""

    request_id: UUID
    adapter_id: str
    model: str
    content: str
    finish_reason: ModelFinishReason
    usage: ModelUsage
    untrusted: bool = field(default=True, init=False)

    def __post_init__(self) -> None:
        if not self.content:
            raise ModelContractError("A model response must contain text.")


@runtime_checkable
class ModelAdapter(Protocol):
    """Narrow adapter capability: text completion only, without tool access."""

    @property
    def descriptor(self) -> ModelAdapterDescriptor:
        """Return static metadata used for routing and policy checks."""

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Return untrusted text for one immutable request."""


class FakeModelAdapter:
    """Deterministic in-process adapter for offline development and tests."""

    def __init__(
        self,
        *,
        adapter_id: str = "offline-fake",
        capabilities: frozenset[ModelCapability] | None = None,
    ) -> None:
        self._descriptor = ModelAdapterDescriptor(
            adapter_id=adapter_id,
            provider="sagent",
            model="deterministic-fake-v1",
            capabilities=capabilities
            or frozenset({ModelCapability.CHAT, ModelCapability.CODING}),
            transport=ModelTransport.IN_PROCESS,
            simulated=True,
        )

    @property
    def descriptor(self) -> ModelAdapterDescriptor:
        return self._descriptor

    def complete(self, request: ModelRequest) -> ModelResponse:
        if request.capability not in self.descriptor.capabilities:
            raise ModelContractError("Fake adapter does not support this capability.")
        if request.stream:
            raise ModelContractError("Fake adapter does not support streaming.")

        canonical = json.dumps(
            {
                "capability": request.capability.value,
                "parts": [
                    {"content": part.content, "source": part.source.value}
                    for part in request.parts
                ],
                "temperature": request.temperature,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        full_content = (
            f"Offline-Simulation {digest}: Die {request.capability.value}-Anfrage wurde "
            "deterministisch verarbeitet. Es gab keinen Modell-, Netzwerk- oder Tool-Aufruf."
        )
        max_characters = max(1, request.max_output_tokens * 4)
        truncated = len(full_content) > max_characters
        content = full_content[:max_characters]
        input_characters = sum(len(part.content) for part in request.parts)
        return ModelResponse(
            request_id=request.request_id,
            adapter_id=self.descriptor.adapter_id,
            model=self.descriptor.model,
            content=content,
            finish_reason=ModelFinishReason.LENGTH if truncated else ModelFinishReason.STOP,
            usage=ModelUsage(
                input_tokens=max(1, math.ceil(input_characters / 4)),
                output_tokens=max(1, math.ceil(len(content) / 4)),
            ),
        )


class ModelRouter:
    """Route requests only to explicitly registered and allowed transports."""

    def __init__(
        self,
        adapters: Sequence[ModelAdapter],
        routes: Mapping[ModelCapability, str],
        *,
        allowed_transports: frozenset[ModelTransport] | None = None,
        allow_non_simulated: bool = False,
        max_parts: int = 32,
        max_input_characters: int = 64_000,
        max_output_characters: int = 32_000,
    ) -> None:
        if not adapters:
            raise ModelContractError("At least one model adapter is required.")
        if max_parts < 1 or max_input_characters < 1 or max_output_characters < 1:
            raise ModelContractError("Model resource limits must be positive.")

        registered: dict[str, ModelAdapter] = {}
        for adapter in adapters:
            if not isinstance(adapter, ModelAdapter):
                raise ModelContractError("Registered adapter does not implement ModelAdapter.")
            adapter_id = adapter.descriptor.adapter_id
            if adapter_id in registered:
                raise ModelContractError(f"Duplicate model adapter: {adapter_id}")
            registered[adapter_id] = adapter

        normalized_routes = dict(routes)
        for capability, adapter_id in normalized_routes.items():
            adapter = registered.get(adapter_id)
            if adapter is None:
                raise ModelContractError("Model route references an unknown adapter.")
            if capability not in adapter.descriptor.capabilities:
                raise ModelContractError("Model route targets an unsupported capability.")

        self._adapters = MappingProxyType(registered)
        self._routes = MappingProxyType(normalized_routes)
        self.allowed_transports = (
            frozenset({ModelTransport.IN_PROCESS})
            if allowed_transports is None
            else allowed_transports
        )
        self.allow_non_simulated = allow_non_simulated
        self.max_parts = max_parts
        self.max_input_characters = max_input_characters
        self.max_output_characters = max_output_characters

    def list_adapters(self) -> tuple[ModelAdapterDescriptor, ...]:
        """Return immutable review metadata without adapter internals."""

        return tuple(
            self._adapters[adapter_id].descriptor for adapter_id in sorted(self._adapters)
        )

    def complete(self, request: ModelRequest, *, adapter_id: str | None = None) -> ModelResponse:
        """Validate, route, execute, and revalidate one text-only request."""

        self._validate_request(request)
        selected_id = adapter_id or self._routes.get(request.capability)
        if selected_id is None:
            raise ModelRouteNotFoundError(
                f"No adapter is configured for {request.capability.value}."
            )
        try:
            adapter = self._adapters[selected_id]
        except KeyError as error:
            raise ModelRouteNotFoundError("Requested model adapter is not registered.") from error

        descriptor = adapter.descriptor
        if request.capability not in descriptor.capabilities:
            raise ModelRouteNotFoundError("Adapter does not support the requested capability.")
        if descriptor.transport not in self.allowed_transports:
            raise ModelTransportBlockedError(
                f"Model transport {descriptor.transport.value} is not allowed."
            )
        if not descriptor.simulated and not self.allow_non_simulated:
            raise ModelAdapterBlockedError(
                "Non-simulated model adapters require an explicit runtime enablement."
            )
        if request.stream and not descriptor.supports_streaming:
            raise ModelContractError("Selected adapter does not support streaming.")

        try:
            response = adapter.complete(request)
        except ModelRuntimeError:
            raise
        except Exception as error:
            raise ModelAdapterExecutionError("Model adapter execution failed.") from error

        self._validate_response(request, descriptor, response)
        return response

    def _validate_request(self, request: ModelRequest) -> None:
        if len(request.parts) > self.max_parts:
            raise ModelContractError("Model request exceeds the configured part limit.")
        input_characters = sum(len(part.content) for part in request.parts)
        if input_characters > self.max_input_characters:
            raise ModelContractError("Model request exceeds the configured input limit.")

    def _validate_response(
        self,
        request: ModelRequest,
        descriptor: ModelAdapterDescriptor,
        response: ModelResponse,
    ) -> None:
        if response.request_id != request.request_id:
            raise ModelResponseError("Model response does not match the request.")
        if response.adapter_id != descriptor.adapter_id or response.model != descriptor.model:
            raise ModelResponseError("Model response identity does not match the adapter.")
        if len(response.content) > self.max_output_characters:
            raise ModelResponseError("Model response exceeds the configured output limit.")
        if response.untrusted is not True:
            raise ModelResponseError("Model response must remain untrusted.")
