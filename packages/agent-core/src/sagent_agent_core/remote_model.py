"""Remote (cloud) model adapter for OpenAI-compatible APIs."""

import json
import re
from collections.abc import Sequence

import httpx

from sagent_agent_core.model_runtime import (
    ModelAdapter,
    ModelAdapterDescriptor,
    ModelCancellationToken,
    ModelCapability,
    ModelContractError,
    ModelFinishReason,
    ModelInputPart,
    ModelInputSource,
    ModelRequest,
    ModelResponse,
    ModelResponseError,
    ModelRuntimeError,
    ModelTransport,
    ModelUsage,
)


class RemoteModelConnectionError(ModelRuntimeError):
    """Raised when the remote API cannot be reached."""


class RemoteModelTimeoutError(ModelRuntimeError):
    """Raised when the remote API exceeds a configured timeout."""


class RemoteModelProtocolError(ModelResponseError):
    """Raised when the remote server returns an unexpected response."""


class RemoteOpenAIChatAdapter:
    """Non-streaming text adapter for remote OpenAI-compatible APIs.

    Unlike LoopbackOpenAIChatAdapter, this adapter has no loopback port
    restriction and sends an Authorization header with the configured API key.
    """

    _MODEL_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,255}$")

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        *,
        adapter_id: str = "remote-openai",
        provider: str = "openai-compatible",
        connect_timeout_seconds: float = 10.0,
        read_timeout_seconds: float = 300.0,
    ) -> None:
        if not self._MODEL_IDENTIFIER.match(model):
            raise ModelContractError(f"Invalid model identifier: {model}")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self._timeout = httpx.Timeout(
            connect=connect_timeout_seconds,
            read=read_timeout_seconds,
            write=connect_timeout_seconds,
            pool=connect_timeout_seconds,
        )
        self._descriptor = ModelAdapterDescriptor(
            adapter_id=adapter_id,
            provider=provider,
            model=model,
            capabilities=frozenset({ModelCapability.CHAT, ModelCapability.CODING}),
            transport=ModelTransport.REMOTE_HTTP,
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
        if cancellation is not None:
            cancellation.raise_if_cancelled()
        if request.stream:
            raise ModelContractError("Remote adapter does not support streaming.")
        if request.capability not in self.descriptor.capabilities:
            raise ModelContractError("Remote adapter does not support this capability.")

        payload = self._build_payload(request)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "sagent-remote-model/0.1",
        }

        url = self._chat_url()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url, json=payload, headers=headers)
        except httpx.ConnectError as e:
            raise RemoteModelConnectionError(str(e)) from e
        except httpx.TimeoutException as e:
            raise RemoteModelTimeoutError(str(e)) from e
        except httpx.HTTPError as e:
            raise RemoteModelProtocolError(str(e)) from e

        if resp.status_code != 200:
            detail = resp.text[:500]
            raise RemoteModelProtocolError(f"HTTP {resp.status_code}: {detail}")

        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            raise RemoteModelProtocolError(f"Invalid JSON response: {e}") from e

        choices = data.get("choices", [])
        if not choices:
            raise RemoteModelProtocolError("No choices in response.")
        choice = choices[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        finish = choice.get("finish_reason", "stop")

        tool_calls = None
        raw_tool_calls = message.get("tool_calls")
        if raw_tool_calls:
            parsed: list[dict] = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                parsed.append({
                    "id": tc.get("id", ""),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": func.get("name", ""),
                        "arguments": func.get("arguments", "{}"),
                    },
                })
            if parsed:
                tool_calls = tuple(parsed)

        usage_data = data.get("usage", {})
        usage = ModelUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
        )
        finish_reason = (
            ModelFinishReason.STOP if finish == "stop"
            else ModelFinishReason.LENGTH if finish == "length"
            else ModelFinishReason.STOP
        )

        if cancellation is not None:
            cancellation.raise_if_cancelled()

        return ModelResponse(
            request_id=request.request_id,
            adapter_id=self.descriptor.adapter_id,
            model=self.descriptor.model,
            content=content,
            finish_reason=finish_reason,
            usage=usage,
            tool_calls=tool_calls,
        )

    def _chat_url(self) -> str:
        if self._descriptor.provider == "google":
            return f"{self.base_url}/v1beta/openai/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def _build_payload(self, request: ModelRequest) -> dict:
        role_map = {
            ModelInputSource.POLICY: "system",
            ModelInputSource.USER: "user",
            ModelInputSource.ASSISTANT: "assistant",
            ModelInputSource.WORKSPACE: "user",
            ModelInputSource.MEMORY: "user",
            ModelInputSource.TOOL_RESULT: "tool",
            ModelInputSource.IMAGE: "user",
        }

        # Collect multi-modal content per-role
        messages: list[dict] = []
        current_role = "user"
        current_content: list[dict] | str = []

        def _flush():
            nonlocal current_content
            if current_content:
                if isinstance(current_content, list) and len(current_content) == 1 and current_content[0]["type"] == "text":
                    messages.append({"role": current_role, "content": current_content[0]["text"]})
                elif isinstance(current_content, list):
                    messages.append({"role": current_role, "content": current_content})
                elif isinstance(current_content, str):
                    messages.append({"role": current_role, "content": current_content})
                current_content = []

        for part in request.parts:
            role = role_map.get(part.source, "user")
            if part.source == ModelInputSource.IMAGE:
                if role != current_role:
                    _flush()
                    current_role = role
                if isinstance(current_content, str):
                    current_content = [{"type": "text", "text": current_content}]
                elif not isinstance(current_content, list):
                    current_content = []
                img_url = part.content if part.content.startswith("data:") else f"data:image/png;base64,{part.content}"
                current_content.append({"type": "image_url", "image_url": {"url": img_url}})
            else:
                if role != current_role or isinstance(current_content, list):
                    _flush()
                    current_role = role
                if isinstance(current_content, list):
                    current_content.append({"type": "text", "text": part.content})
                else:
                    current_content = part.content

        _flush()

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
            "stream": False,
        }
        if request.tools:
            payload["tools"] = list(request.tools)
        return payload
