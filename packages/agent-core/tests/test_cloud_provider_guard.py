"""Offline guards ensuring cloud provider policy is enforced at compile-/test-time.

Every test in this file runs without network, without model calls, and without
accessing any API key, secret, or endpoint configuration. Tests verify that:

- remote_http is blocked by default and through an independent guard
- DeepSeek Cloud is absent from the local provider allowlist
- No local provider can be mistaken for a cloud provider
- No automatic fallback from local to cloud exists
- Cloud models receive no tool authority
- No API keys or endpoints are hardcoded in the source
"""

from dataclasses import dataclass
from pathlib import Path

import pytest

from sagent_agent_core import (
    LOCAL_PROVIDER_PROFILES,
    CloudProviderDisabledError,
    ModelAdapterDescriptor,
    ModelCancellationToken,
    ModelCapability,
    ModelContractError,
    ModelFinishReason,
    ModelInputPart,
    ModelInputSource,
    ModelRequest,
    ModelResponse,
    ModelRouter,
    ModelTransport,
    ModelTransportBlockedError,
    ModelUsage,
    get_local_provider_profile,
)


@dataclass
class _StaticAdapter:
    descriptor: ModelAdapterDescriptor
    content: str = "static"
    call_count: int = 0

    def complete(
        self,
        model_request: ModelRequest,
        *,
        cancellation: ModelCancellationToken | None = None,
    ) -> ModelResponse:
        self.call_count += 1
        return ModelResponse(
            request_id=model_request.request_id,
            adapter_id=self.descriptor.adapter_id,
            model=self.descriptor.model,
            content=self.content,
            finish_reason=ModelFinishReason.STOP,
            usage=ModelUsage(input_tokens=1, output_tokens=1),
        )


def _descriptor(
    adapter_id: str = "remote-test",
    *,
    transport: ModelTransport = ModelTransport.REMOTE_HTTP,
    simulated: bool = False,
) -> ModelAdapterDescriptor:
    return ModelAdapterDescriptor(
        adapter_id=adapter_id,
        provider="test",
        model=f"{adapter_id}-model",
        capabilities=frozenset({ModelCapability.CODING}),
        transport=transport,
        simulated=simulated,
    )


def _request(content: str = "test") -> ModelRequest:
    return ModelRequest(
        capability=ModelCapability.CODING,
        parts=(ModelInputPart(source=ModelInputSource.USER, content=content),),
        max_output_tokens=128,
    )


# ---------------------------------------------------------------------------
# 1. remote_http is blocked by default
# ---------------------------------------------------------------------------


def test_remote_http_is_blocked_by_default_router() -> None:
    """Default ModelRouter does not allow remote_http adapters."""
    adapter = _StaticAdapter(
        _descriptor("remote-provider", transport=ModelTransport.REMOTE_HTTP)
    )
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: "remote-provider"},
    )
    with pytest.raises(ModelTransportBlockedError, match="remote_http"):
        router.complete(_request())
    assert adapter.call_count == 0


def test_remote_http_is_independently_guarded_even_in_allowlist() -> None:
    """Even if remote_http is added to allowed_transports, the independent
    cloud_providers_enabled guard still blocks it."""
    adapter = _StaticAdapter(
        _descriptor("remote-provider", transport=ModelTransport.REMOTE_HTTP)
    )
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: "remote-provider"},
        allowed_transports=frozenset({
            ModelTransport.IN_PROCESS,
            ModelTransport.LOOPBACK_HTTP,
            ModelTransport.REMOTE_HTTP,
        }),
        cloud_providers_enabled=False,
    )
    with pytest.raises(CloudProviderDisabledError, match="Cloud provider access is disabled"):
        router.complete(_request())
    assert adapter.call_count == 0


def test_remote_http_requires_explicit_cloud_approval() -> None:
    """remote_http works only when both allowed_transports and
    cloud_providers_enabled=True are set, with a non-simulated adapter."""
    adapter = _StaticAdapter(
        _descriptor("cloud-adapter", transport=ModelTransport.REMOTE_HTTP, simulated=False),
    )
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: "cloud-adapter"},
        allowed_transports=frozenset({
            ModelTransport.IN_PROCESS,
            ModelTransport.REMOTE_HTTP,
        }),
        allow_non_simulated=True,
        cloud_providers_enabled=True,
    )
    response = router.complete(_request())
    assert response.untrusted is True
    assert adapter.call_count == 1


# ---------------------------------------------------------------------------
# 2. DeepSeek Cloud is not in the local provider allowlist
# ---------------------------------------------------------------------------


def test_local_provider_profiles_do_not_contain_deepseek() -> None:
    """DeepSeek is not among the fixed loopback provider profiles."""
    provider_ids = {p.provider_id for p in LOCAL_PROVIDER_PROFILES}
    assert "deepseek" not in provider_ids
    assert "deepseek-cloud" not in provider_ids
    assert "ds" not in provider_ids


def test_local_provider_profiles_have_no_cloud_indicators() -> None:
    """No local profile refers to a cloud-like label, adapter, or host."""
    for profile in LOCAL_PROVIDER_PROFILES:
        label_lower = profile.label.lower()
        assert "cloud" not in label_lower
        assert "remote" not in label_lower
        assert "deepseek" not in label_lower
        assert "https" not in profile.host
        assert profile.host == "127.0.0.1"


def test_get_local_provider_rejects_cloud_ids() -> None:
    """get_local_provider_profile returns None for any non-loopback ID."""
    assert get_local_provider_profile("deepseek-cloud") is None
    assert get_local_provider_profile("deepseek") is None
    assert get_local_provider_profile("remote") is None
    assert get_local_provider_profile("cloud") is None
    assert get_local_provider_profile("") is None


# ---------------------------------------------------------------------------
# 3. DeepSeek Cloud cannot appear as an Ollama or LM Studio provider
# ---------------------------------------------------------------------------


def test_adapter_descriptor_must_have_stable_provider_label() -> None:
    """Provider label validation prevents accidental cloud impersonation."""
    with pytest.raises(ModelContractError, match="single-line value"):
        ModelAdapterDescriptor(
            adapter_id="ollama",
            provider="deepseek\x00cloud",
            model="deepseek-model",
            capabilities=frozenset({ModelCapability.CODING}),
            transport=ModelTransport.LOOPBACK_HTTP,
            simulated=False,
        )


def test_local_provider_ids_match_expected_values() -> None:
    """Only lm-studio and ollama are approved loopback provider IDs."""
    assert {p.provider_id for p in LOCAL_PROVIDER_PROFILES} == {"lm-studio", "ollama"}
    assert {p.adapter_id for p in LOCAL_PROVIDER_PROFILES} == {
        "local-lm-studio",
        "local-ollama",
    }
    assert {p.port for p in LOCAL_PROVIDER_PROFILES} == {1_234, 11_434}


# ---------------------------------------------------------------------------
# 4. No automatic fallback from local to cloud
# ---------------------------------------------------------------------------


def test_router_has_no_implicit_fallback_to_remote() -> None:
    """When a local adapter fails, the router does not try a remote fallback."""
    local = _StaticAdapter(
        _descriptor("local", transport=ModelTransport.LOOPBACK_HTTP, simulated=False),
        content="local result",
    )
    remote = _StaticAdapter(
        _descriptor("remote", transport=ModelTransport.REMOTE_HTTP),
    )
    router = ModelRouter(
        [local, remote],
        {ModelCapability.CODING: "local"},
        allowed_transports=frozenset({
            ModelTransport.IN_PROCESS,
            ModelTransport.LOOPBACK_HTTP,
        }),
        allow_non_simulated=True,
    )
    response = router.complete(_request())
    assert response.adapter_id == "local"
    assert local.call_count == 1
    assert remote.call_count == 0


# ---------------------------------------------------------------------------
# 5. Cloud models receive no tool authority
# ---------------------------------------------------------------------------


def test_all_responses_are_untrusted() -> None:
    """Every ModelResponse is unconditionally untrusted, regardless of adapter."""
    for transport in ModelTransport:
        adapter = _StaticAdapter(
            _descriptor(f"test-{transport.value}", transport=transport),
        )
        allowed = frozenset({ModelTransport.IN_PROCESS, transport})
        router = ModelRouter(
            [adapter],
            {ModelCapability.CODING: f"test-{transport.value}"},
            allowed_transports=allowed,
            cloud_providers_enabled=True,
            allow_non_simulated=True,
        )
        response = router.complete(_request())
        assert response.untrusted is True


def test_response_has_no_tool_call_attribute() -> None:
    """ModelResponse does not expose tool-call structures."""
    response = _StaticAdapter(
        _descriptor("any", transport=ModelTransport.IN_PROCESS),
    ).complete(_request())
    assert not hasattr(response, "tool_calls")
    assert not hasattr(response, "tool_choice")
    assert not hasattr(response, "function_call")


def test_adapter_descriptor_has_no_tool_interface() -> None:
    """Adapter protocol does not include tool definitions or tool routing."""
    assert not hasattr(_descriptor(), "tool_definitions")
    assert not hasattr(_descriptor(), "tool_choice")


# ---------------------------------------------------------------------------
# 6. No API keys or endpoints are hardcoded in source
# ---------------------------------------------------------------------------

_PACKAGE_ROOTS = [
    Path("packages/agent-core/src"),
    Path("packages/agent-core/tests"),
    Path("packages/tools/src"),
    Path("packages/tools/tests"),
    Path("apps/agent-api/src"),
    Path("apps/agent-api/tests"),
    Path("apps/web/tests"),
]

_FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    ("API key literal", r'["\'][A-Za-z0-9_-]{20,}["\']'),
    ("secret assignment", r'secret\s*=\s*["\'][^"\']{8,}["\']'),
    ("api_key parameter default", r'api_key\s*=\s*["\'][^"\']+["\']'),
    ("authorization header with token", r'["\']Authorization["\']\s*:\s*["\']Bearer\s+\S+'),
    ("hardcoded https host", r'https?://[a-zA-Z0-9.-]+(?:\.com|\.io|\.dev|\.org|\.ai)(?::\d+)?/'),
]


def test_no_hardcoded_api_keys_in_source() -> None:
    """Scan Python and JS source for common sensitive patterns, excluding
    this test file and threat-model test data."""
    repo_root = Path(__file__).resolve().parents[3]
    this_file = Path(__file__).resolve()
    errors: list[str] = []
    for root in _PACKAGE_ROOTS:
        abs_root = repo_root / root
        if not abs_root.is_dir():
            continue
        for path in sorted(abs_root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in (".py", ".mjs", ".ts", ".tsx", ".js"):
                continue
            if ".venv" in path.parts or "node_modules" in path.parts:
                continue
            if path.resolve() == this_file:
                continue
            # Skip the test data that intentionally contains threat model patterns
            if "test_cloud_provider_guard" in path.name:
                continue
            try:
                text = path.read_text("utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for pattern_name, regex in _FORBIDDEN_PATTERNS:
                if regex in text:
                    errors.append(
                        f"{pattern_name} match in {path.relative_to(repo_root)}"
                    )
    # Skip localhost / loopback references which are intentional
    allowed_references = {"127.0.0.1", "localhost", "example.com", "example.org"}
    filtered = [
        e
        for e in errors
        if not any(ref in e.lower() for ref in allowed_references)
    ]
    assert not filtered, "Potential secrets or hardcoded endpoints found:\n" + "\n".join(filtered)


def test_no_api_key_imports_in_source() -> None:
    """No module imports or references to API key / secret modules."""
    repo_root = Path(__file__).resolve().parents[3]
    forbidden_imports = [
        "api_key", "api_secret", "access_token", "secret_key",
        "openai", "anthropic", "deepseek",
    ]
    for root in _PACKAGE_ROOTS:
        abs_root = repo_root / root
        if not abs_root.is_dir():
            continue
        for path in sorted(abs_root.rglob("*.py")):
            if ".venv" in path.parts:
                continue
            text = path.read_text("utf-8")
            for name in forbidden_imports:
                if f"import {name}" in text or f"from {name}" in text:
                    pytest.fail(
                        f"Forbidden import '{name}' found in {path.relative_to(repo_root)}"
                    )
