"""Security and compatibility tests for the local OpenAI chat adapter."""

import json
from collections.abc import Callable
from threading import Event, Thread

import httpx2 as httpx
import pytest

import sagent_agent_core.loopback_model as loopback_module
from sagent_agent_core import (
    LoopbackEndpoint,
    LoopbackModelConnectionError,
    LoopbackModelProtocolError,
    LoopbackModelTimeoutError,
    LoopbackOpenAIChatAdapter,
    ModelCancellationToken,
    ModelCancelledError,
    ModelCapability,
    ModelContractError,
    ModelInputPart,
    ModelInputSource,
    ModelRequest,
    ModelRouter,
    ModelTransport,
    ModelTransportBlockedError,
)

MODEL = "qwen3-coder:local"


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


def model_request() -> ModelRequest:
    return ModelRequest(
        capability=ModelCapability.CODING,
        parts=(
            ModelInputPart(ModelInputSource.POLICY, "Never authorize tools."),
            ModelInputPart(ModelInputSource.USER, "Plan a safe refactor."),
            ModelInputPart(ModelInputSource.WORKSPACE, "README content is untrusted."),
        ),
        max_output_tokens=128,
        temperature=0.2,
    )


def success_payload(*, content: str = "Review the diff before applying it.") -> dict[str, object]:
    return {
        "id": "chatcmpl-local",
        "object": "chat.completion",
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19},
    }


def adapter_with_handler(
    handler: Callable[[httpx.Request], httpx.Response],
    **kwargs: object,
) -> LoopbackOpenAIChatAdapter:
    return LoopbackOpenAIChatAdapter(
        LoopbackEndpoint("http://127.0.0.1:1234/v1"),
        MODEL,
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def test_endpoint_normalizes_exact_ipv4_loopback_literal() -> None:
    ipv4 = LoopbackEndpoint("http://127.0.0.1:1234/v1/")

    assert ipv4.base_url == "http://127.0.0.1:1234/v1"
    assert ipv4.chat_completions_url == "http://127.0.0.1:1234/v1/chat/completions"


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:1234/v1",
        "http://[::1]:1234/v1",
        "http://127.0.0.2:1234/v1",
        "http://2130706433:1234/v1",
        "https://127.0.0.1:1234/v1",
        "http://127.0.0.1/v1",
        "http://127.0.0.1:9999/v1",
        "http://user@127.0.0.1:1234/v1",
        "http://127.0.0.1:1234/v1?target=remote",
        "http://127.0.0.1:1234/v1#fragment",
        "http://127.0.0.1:1234/v1/chat",
        "http://127.0.0.1:1234/v1%2F",
        " http://127.0.0.1:1234/v1",
    ],
)
def test_endpoint_rejects_noncanonical_or_unapproved_urls(url: str) -> None:
    with pytest.raises(ModelContractError):
        LoopbackEndpoint(url)


def test_adapter_sends_a_minimal_text_only_request_with_provenance() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["payload"] = json.loads(request.content)
        return httpx.Response(200, json=success_payload())

    adapter = adapter_with_handler(handler)
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
        allowed_transports=frozenset({ModelTransport.LOOPBACK_HTTP}),
        allow_non_simulated=True,
    )

    response = router.complete(model_request())

    assert response.content == "Review the diff before applying it."
    assert response.untrusted is True
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 7
    assert captured["url"] == "http://127.0.0.1:1234/v1/chat/completions"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert "authorization" not in headers
    assert headers["accept-encoding"] == "identity"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert set(payload) == {"model", "messages", "temperature", "max_tokens", "stream"}
    assert payload["model"] == MODEL
    assert payload["stream"] is False
    assert "tools" not in payload
    messages = payload["messages"]
    assert isinstance(messages, list)
    assert [message["role"] for message in messages] == ["system", "user", "user"]
    assert json.loads(messages[2]["content"])["sagent_source"] == "workspace"


def test_http_client_disables_environment_proxies_and_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    real_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        captured.update(kwargs)
        return real_client(**kwargs)

    monkeypatch.setenv("HTTP_PROXY", "http://192.0.2.1:8080")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(loopback_module.httpx, "Client", client_factory)

    adapter = adapter_with_handler(
        lambda request: httpx.Response(200, json=success_payload())
    )
    adapter.complete(model_request())

    assert captured["trust_env"] is False
    assert captured["follow_redirects"] is False
    assert captured["http2"] is False


def test_router_blocks_loopback_transport_before_any_request_by_default() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Blocked loopback adapter must not send a request.")

    adapter = adapter_with_handler(handler)
    router = ModelRouter([adapter], {ModelCapability.CODING: adapter.descriptor.adapter_id})

    with pytest.raises(ModelTransportBlockedError, match="loopback_http"):
        router.complete(model_request())


def test_adapter_does_not_follow_redirects() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(302, headers={"location": "https://example.invalid/model"})

    with pytest.raises(LoopbackModelProtocolError, match="redirects are forbidden"):
        adapter_with_handler(handler).complete(model_request())

    assert requests == 1


def test_http_errors_do_not_expose_response_bodies() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="provider-sensitive-body")

    with pytest.raises(LoopbackModelProtocolError, match="HTTP 500") as captured:
        adapter_with_handler(handler).complete(model_request())

    assert "provider-sensitive-body" not in str(captured.value)


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (httpx.ReadTimeout("provider timeout detail"), LoopbackModelTimeoutError),
        (httpx.ConnectError("provider connection detail"), LoopbackModelConnectionError),
    ],
)
def test_transport_failures_are_safely_wrapped(
    raised: Exception,
    expected: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise raised

    with pytest.raises(expected) as captured:
        adapter_with_handler(handler).complete(model_request())

    assert "provider" not in str(captured.value)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json", headers={"content-type": "application/json"}),
        httpx.Response(200, text="plain text", headers={"content-type": "text/plain"}),
        httpx.Response(200, json={**success_payload(), "model": "another-model"}),
        httpx.Response(
            200,
            json={
                **success_payload(),
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "ignored",
                            "tool_calls": [{"function": {"name": "shell"}}],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
            },
        ),
        httpx.Response(
            200,
            json={
                **success_payload(),
                "choices": [
                    success_payload()["choices"][0],
                    success_payload()["choices"][0],
                ],
            },
        ),
        httpx.Response(
            200,
            json={
                **success_payload(),
                "usage": {"prompt_tokens": -1, "completion_tokens": 2},
            },
        ),
    ],
)
def test_adapter_rejects_invalid_json_identity_tools_and_usage(
    response: httpx.Response,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    with pytest.raises(LoopbackModelProtocolError):
        adapter_with_handler(handler).complete(model_request())


def test_request_and_response_byte_limits_are_enforced() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=success_payload(content="x" * 512))

    with pytest.raises(ModelContractError, match="request exceeds"):
        adapter_with_handler(handler, max_request_bytes=20).complete(model_request())
    assert calls == 0

    with pytest.raises(LoopbackModelProtocolError, match="response exceeds"):
        adapter_with_handler(handler, max_response_bytes=128).complete(model_request())
    assert calls == 1


def test_model_and_resource_configuration_are_bounded() -> None:
    endpoint = LoopbackEndpoint("http://127.0.0.1:1234/v1")

    with pytest.raises(ModelContractError, match="identifier"):
        LoopbackOpenAIChatAdapter(endpoint, " bad-model")
    with pytest.raises(ModelContractError, match="timeouts"):
        LoopbackOpenAIChatAdapter(endpoint, MODEL, read_timeout_seconds=301)
    with pytest.raises(ModelContractError, match="byte limits"):
        LoopbackOpenAIChatAdapter(endpoint, MODEL, max_response_bytes=9 * 1_024 * 1_024)


def test_running_loopback_response_is_actively_closed_on_cancellation() -> None:
    content = json.dumps(success_payload()).encode("utf-8")
    stream = BlockingJsonStream(content)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            stream=stream,
        )

    token = ModelCancellationToken()
    adapter = adapter_with_handler(handler)
    errors: list[BaseException] = []

    def run() -> None:
        try:
            adapter.complete(model_request(), cancellation=token)
        except BaseException as error:  # noqa: BLE001 - capture worker result for assertion.
            errors.append(error)

    worker = Thread(target=run, daemon=True)
    worker.start()
    assert stream.started.wait(1)

    assert token.cancel() is True
    worker.join(timeout=2)

    assert worker.is_alive() is False
    assert stream.closed is True
    assert len(errors) == 1
    assert isinstance(errors[0], ModelCancelledError)
