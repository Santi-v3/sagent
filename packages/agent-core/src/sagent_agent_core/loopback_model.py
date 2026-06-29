"""Strict OpenAI-compatible chat adapter for explicitly allowed loopback endpoints."""

import json
import math
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx2 as httpx

from sagent_agent_core.model_runtime import (
    ModelAdapterDescriptor,
    ModelCancellationToken,
    ModelCancelledError,
    ModelCapability,
    ModelContractError,
    ModelFinishReason,
    ModelInputSource,
    ModelRequest,
    ModelResponse,
    ModelResponseError,
    ModelRuntimeError,
    ModelTransport,
    ModelUsage,
)


class LoopbackModelError(ModelRuntimeError):
    """Base class for safe local model transport failures."""


class LoopbackModelConnectionError(LoopbackModelError):
    """Raised when the allowlisted local model server cannot be reached."""


class LoopbackModelTimeoutError(LoopbackModelError):
    """Raised when the local model server exceeds a configured timeout."""


class LoopbackModelProtocolError(ModelResponseError):
    """Raised when the local server violates the bounded response contract."""


@dataclass(frozen=True, slots=True)
class LoopbackEndpoint:
    """Canonical HTTP base URL restricted to an explicit loopback port allowlist."""

    base_url: str
    allowed_ports: frozenset[int] = frozenset({1_234, 11_434})

    def __post_init__(self) -> None:
        if not self.allowed_ports or any(
            isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65_535
            for port in self.allowed_ports
        ):
            raise ModelContractError("Loopback allowed_ports must contain valid TCP ports.")
        if self.base_url != self.base_url.strip():
            raise ModelContractError("Loopback base URL must not contain surrounding whitespace.")

        try:
            parsed = urlsplit(self.base_url)
            port = parsed.port
        except ValueError as error:
            raise ModelContractError("Loopback base URL is malformed.") from error
        if parsed.scheme != "http":
            raise ModelContractError("Loopback model transport requires plain HTTP.")
        if parsed.username is not None or parsed.password is not None:
            raise ModelContractError("Loopback base URL cannot contain credentials.")
        if parsed.query or parsed.fragment:
            raise ModelContractError("Loopback base URL cannot contain query or fragment data.")
        if port is None or port not in self.allowed_ports:
            raise ModelContractError("Loopback model port is not explicitly allowed.")
        if parsed.hostname != "127.0.0.1":
            raise ModelContractError("Only the exact IPv4 loopback literal is allowed.")
        authority = f"127.0.0.1:{port}"
        if parsed.netloc != authority or parsed.path not in {"/v1", "/v1/"}:
            raise ModelContractError("Loopback base URL must be canonical and end at /v1.")

        object.__setattr__(self, "base_url", f"http://{authority}/v1")

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"


class LoopbackOpenAIChatAdapter:
    """Non-streaming text adapter with no redirects, proxies, credentials, or tools."""

    _MODEL_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,255}$")
    _MAX_CONFIGURED_TIMEOUT = 300.0
    _MAX_CONFIGURED_BYTES = 8 * 1_024 * 1_024

    def __init__(
        self,
        endpoint: LoopbackEndpoint,
        model: str,
        *,
        adapter_id: str = "local-openai-chat",
        provider: str = "local-openai-compatible",
        connect_timeout_seconds: float = 2.0,
        read_timeout_seconds: float = 120.0,
        write_timeout_seconds: float = 10.0,
        pool_timeout_seconds: float = 2.0,
        max_request_bytes: int = 256 * 1_024,
        max_response_bytes: int = 1_024 * 1_024,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._validate_model(model)
        timeouts = (
            connect_timeout_seconds,
            read_timeout_seconds,
            write_timeout_seconds,
            pool_timeout_seconds,
        )
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not 0 < value <= self._MAX_CONFIGURED_TIMEOUT
            for value in timeouts
        ):
            raise ModelContractError("Loopback timeouts must be positive and at most 300s.")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= self._MAX_CONFIGURED_BYTES
            for value in (max_request_bytes, max_response_bytes)
        ):
            raise ModelContractError("Loopback byte limits must be between 1 byte and 8 MiB.")

        self.endpoint = endpoint
        self.model = model
        self.max_request_bytes = max_request_bytes
        self.max_response_bytes = max_response_bytes
        self._transport = transport
        self._timeout = httpx.Timeout(
            connect=connect_timeout_seconds,
            read=read_timeout_seconds,
            write=write_timeout_seconds,
            pool=pool_timeout_seconds,
        )
        self._descriptor = ModelAdapterDescriptor(
            adapter_id=adapter_id,
            provider=provider,
            model=model,
            capabilities=frozenset({ModelCapability.CHAT, ModelCapability.CODING}),
            transport=ModelTransport.LOOPBACK_HTTP,
            simulated=False,
        )

    @property
    def descriptor(self) -> ModelAdapterDescriptor:
        return self._descriptor

    def complete(
        self,
        request: ModelRequest,
        *,
        cancellation: ModelCancellationToken | None = None,
    ) -> ModelResponse:
        """Send one bounded request and accept only a text chat completion."""

        if cancellation is not None:
            cancellation.raise_if_cancelled()
        if request.stream:
            raise ModelContractError("Loopback streaming is not enabled in MVP 2.B.")
        if request.capability not in self.descriptor.capabilities:
            raise ModelContractError("Loopback adapter does not support this capability.")

        payload = self._request_payload(request)
        request_bytes = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(request_bytes) > self.max_request_bytes:
            raise ModelContractError("Loopback model request exceeds the byte limit.")

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Content-Type": "application/json",
            "User-Agent": "sagent-local-model/0.1",
        }
        client = httpx.Client(
            transport=self._transport,
            timeout=self._timeout,
            trust_env=False,
            follow_redirects=False,
            http1=True,
            http2=False,
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
        )
        unregister_client = (
            cancellation.add_cancel_callback(client.close)
            if cancellation is not None
            else lambda: None
        )
        try:
            with client:
                if cancellation is not None:
                    cancellation.raise_if_cancelled()
                with client.stream(
                    "POST",
                    self.endpoint.chat_completions_url,
                    content=request_bytes,
                    headers=headers,
                ) as response:
                    unregister_response = (
                        cancellation.add_cancel_callback(response.close)
                        if cancellation is not None
                        else lambda: None
                    )
                    try:
                        body = self._read_response(response, cancellation)
                    finally:
                        unregister_response()
        except (LoopbackModelError, LoopbackModelProtocolError) as error:
            if cancellation is not None and cancellation.is_cancelled:
                raise ModelCancelledError("Model request was cancelled.") from error
            raise
        except httpx.TimeoutException as error:
            if cancellation is not None and cancellation.is_cancelled:
                raise ModelCancelledError("Model request was cancelled.") from error
            raise LoopbackModelTimeoutError("Local model request timed out.") from error
        except httpx.HTTPError as error:
            if cancellation is not None and cancellation.is_cancelled:
                raise ModelCancelledError("Model request was cancelled.") from error
            raise LoopbackModelConnectionError("Local model server is unavailable.") from error
        except Exception as error:
            if cancellation is not None and cancellation.is_cancelled:
                raise ModelCancelledError("Model request was cancelled.") from error
            raise
        finally:
            unregister_client()

        if cancellation is not None:
            cancellation.raise_if_cancelled()
        return self._parse_response(request, body)

    def _request_payload(self, request: ModelRequest) -> dict[str, object]:
        messages = []
        for part in request.parts:
            role = "system" if part.source is ModelInputSource.POLICY else "user"
            messages.append(
                {
                    "role": role,
                    "content": json.dumps(
                        {"content": part.content, "sagent_source": part.source.value},
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                }
            )
        return {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_output_tokens,
            "stream": False,
        }

    def _read_response(
        self,
        response: httpx.Response,
        cancellation: ModelCancellationToken | None,
    ) -> bytes:
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        if 300 <= response.status_code < 400:
            raise LoopbackModelProtocolError("Local model redirects are forbidden.")
        if response.status_code != 200:
            raise LoopbackModelProtocolError(
                f"Local model server returned HTTP {response.status_code}."
            )
        content_type = response.headers.get("content-type", "").partition(";")[0].strip().lower()
        if content_type != "application/json":
            raise LoopbackModelProtocolError("Local model response must be JSON.")
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError as error:
                raise LoopbackModelProtocolError(
                    "Local model Content-Length is invalid."
                ) from error
            if declared_length < 0 or declared_length > self.max_response_bytes:
                raise LoopbackModelProtocolError("Local model response exceeds the byte limit.")

        body = bytearray()
        for chunk in response.iter_bytes():
            if cancellation is not None:
                cancellation.raise_if_cancelled()
            if len(body) + len(chunk) > self.max_response_bytes:
                raise LoopbackModelProtocolError("Local model response exceeds the byte limit.")
            body.extend(chunk)
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        if not body:
            raise LoopbackModelProtocolError("Local model response is empty.")
        return bytes(body)

    def _parse_response(self, request: ModelRequest, body: bytes) -> ModelResponse:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise LoopbackModelProtocolError("Local model returned invalid JSON.") from error
        if not isinstance(payload, dict):
            raise LoopbackModelProtocolError("Local model response must be an object.")
        if payload.get("model") != self.model:
            raise LoopbackModelProtocolError("Local model response identity does not match.")

        choices = payload.get("choices")
        if (
            not isinstance(choices, list)
            or len(choices) != 1
            or not isinstance(choices[0], dict)
        ):
            raise LoopbackModelProtocolError("Local model response has no valid choice.")
        choice = choices[0]
        if choice.get("index") != 0:
            raise LoopbackModelProtocolError("Local model choice index is invalid.")
        message = choice.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            raise LoopbackModelProtocolError("Local model response has no assistant message.")
        if message.get("tool_calls") or message.get("function_call"):
            raise LoopbackModelProtocolError("Local model tool calls are not allowed.")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LoopbackModelProtocolError("Local model response has no text content.")

        finish_reason_value = choice.get("finish_reason")
        if finish_reason_value == "stop":
            finish_reason = ModelFinishReason.STOP
        elif finish_reason_value == "length":
            finish_reason = ModelFinishReason.LENGTH
        else:
            raise LoopbackModelProtocolError("Local model finish reason is not allowed.")

        usage = self._parse_usage(payload.get("usage"), request, content)
        return ModelResponse(
            request_id=request.request_id,
            adapter_id=self.descriptor.adapter_id,
            model=self.descriptor.model,
            content=content,
            finish_reason=finish_reason,
            usage=usage,
        )

    @staticmethod
    def _parse_usage(value: object, request: ModelRequest, content: str) -> ModelUsage:
        if value is None:
            input_characters = sum(len(part.content) for part in request.parts)
            return ModelUsage(
                input_tokens=max(1, math.ceil(input_characters / 4)),
                output_tokens=max(1, math.ceil(len(content) / 4)),
            )
        if not isinstance(value, dict):
            raise LoopbackModelProtocolError("Local model usage is malformed.")
        input_tokens = value.get("prompt_tokens")
        output_tokens = value.get("completion_tokens")
        if any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in (input_tokens, output_tokens)
        ):
            raise LoopbackModelProtocolError("Local model token usage is malformed.")
        return ModelUsage(input_tokens=input_tokens, output_tokens=output_tokens)

    @classmethod
    def _validate_model(cls, model: str) -> None:
        if not cls._MODEL_IDENTIFIER.fullmatch(model):
            raise ModelContractError("Local model identifier must be a bounded single line.")
