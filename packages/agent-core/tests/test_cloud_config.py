"""Offline tests for the disabled cloud-provider configuration contract."""

from pathlib import Path

import pytest

from sagent_agent_core import (
    CloudApprovalScope,
    CloudProviderConfig,
    CloudProviderConfigError,
    CloudProviderConfigStatus,
    CloudProviderConfigValidation,
    CloudSecretsSource,
    FakeModelAdapter,
    ModelCapability,
    ModelRouter,
    ModelTransport,
    validate_cloud_provider_config,
)


def test_default_config_is_disabled_and_not_configured() -> None:
    config = CloudProviderConfig()
    assert config.provider_id == "deepseek-cloud"
    assert config.enabled is False
    assert config.status is CloudProviderConfigStatus.NOT_CONFIGURED
    assert config.secrets_source is CloudSecretsSource.NOT_CONFIGURED
    assert config.endpoint_configured is False


def test_deepseek_env_reference_metadata_still_remains_disabled() -> None:
    config = CloudProviderConfig(
        secrets_source=CloudSecretsSource.ENV_REFERENCE_ONLY,
        status=CloudProviderConfigStatus.DISABLED,
    )
    assert config.enabled is False
    assert config.status is CloudProviderConfigStatus.DISABLED


@pytest.mark.parametrize("provider_id", ["ollama", "lm-studio"])
def test_local_providers_are_rejected(provider_id: str) -> None:
    with pytest.raises(CloudProviderConfigError, match="non-cloud provider"):
        CloudProviderConfig(provider_id=provider_id)


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(CloudProviderConfigError, match="non-cloud provider"):
        CloudProviderConfig(provider_id="unknown-cloud")


def test_config_does_not_read_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAGENT_TEST_CLOUD_SECRET", "must-not-be-read")
    config = CloudProviderConfig(
        secrets_source=CloudSecretsSource.ENV_REFERENCE_ONLY,
        status=CloudProviderConfigStatus.DISABLED,
    )
    assert "must-not-be-read" not in repr(config)
    source = Path(
        "packages/agent-core/src/sagent_agent_core/cloud_config.py"
    ).read_text("utf-8")
    assert "import os" not in source
    assert "os.environ" not in source
    assert "os.getenv" not in source


def test_config_contains_no_secret_or_api_key_fields() -> None:
    config = CloudProviderConfig()
    for field_name in ("api_key", "secret", "token", "credential", "env_value"):
        assert not hasattr(config, field_name)


def test_config_contains_no_endpoint_url_host_or_port() -> None:
    config = CloudProviderConfig()
    assert config.endpoint_configured is False
    for field_name in ("endpoint", "url", "host", "port", "base_url"):
        assert not hasattr(config, field_name)


def test_endpoint_configuration_is_rejected() -> None:
    with pytest.raises(CloudProviderConfigError, match="Endpoint configuration"):
        CloudProviderConfig(endpoint_configured=True)


def test_config_cannot_enable_cloud_execution() -> None:
    with pytest.raises(CloudProviderConfigError, match="must remain disabled"):
        CloudProviderConfig(enabled=True)


def test_config_is_immutable() -> None:
    config = CloudProviderConfig()
    with pytest.raises(AttributeError):
        config.enabled = True  # type: ignore[misc]


def test_remote_http_is_classification_only_and_never_allowed() -> None:
    config = CloudProviderConfig()
    validation = validate_cloud_provider_config(config)
    assert config.transport_kind is ModelTransport.REMOTE_HTTP
    assert validation.execution_allowed is False
    assert "remote_http_not_allowed" in validation.blockers


def test_transport_classification_cannot_be_changed() -> None:
    with pytest.raises(CloudProviderConfigError, match="remote_http"):
        CloudProviderConfig(transport_kind=ModelTransport.IN_PROCESS)


def test_config_builds_no_provider_or_router() -> None:
    config = CloudProviderConfig()
    for field_name in ("provider", "adapter", "router", "client", "transport"):
        assert not hasattr(config, field_name)


def test_config_has_no_fallback_metadata() -> None:
    config = CloudProviderConfig()
    for field_name in ("fallback", "fallback_provider", "retry_provider"):
        assert not hasattr(config, field_name)


def test_config_module_has_no_network_client_imports() -> None:
    source = Path(
        "packages/agent-core/src/sagent_agent_core/cloud_config.py"
    ).read_text("utf-8")
    for forbidden in ("import httpx", "import socket", "import urllib", "import requests"):
        assert forbidden not in source


def test_config_does_not_set_cloud_providers_enabled() -> None:
    config = CloudProviderConfig()
    assert not hasattr(config, "cloud_providers_enabled")

    adapter = FakeModelAdapter()
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
    )
    assert router.cloud_providers_enabled is False


def test_config_does_not_extend_allowed_transports() -> None:
    config = CloudProviderConfig()
    assert not hasattr(config, "allowed_transports")

    adapter = FakeModelAdapter()
    router = ModelRouter(
        [adapter],
        {ModelCapability.CODING: adapter.descriptor.adapter_id},
    )
    assert router.allowed_transports == frozenset({ModelTransport.IN_PROCESS})
    assert ModelTransport.REMOTE_HTTP not in router.allowed_transports


def test_explicit_approval_is_always_required() -> None:
    config = CloudProviderConfig()
    assert config.requires_explicit_approval is True
    with pytest.raises(CloudProviderConfigError, match="explicit per-run approval"):
        CloudProviderConfig(requires_explicit_approval=False)


def test_status_matches_secret_source_metadata() -> None:
    with pytest.raises(CloudProviderConfigError, match="Status must be"):
        CloudProviderConfig(status=CloudProviderConfigStatus.DISABLED)


def test_one_run_only_scope_is_always_required() -> None:
    config = CloudProviderConfig()
    assert config.approval_scope is CloudApprovalScope.ONE_RUN_ONLY
    with pytest.raises(CloudProviderConfigError, match="one_run_only"):
        CloudProviderConfig(approval_scope="repeated")  # type: ignore[arg-type]


def test_optional_model_id_is_display_metadata_only() -> None:
    config = CloudProviderConfig(model_id="future-model-display-name")
    assert config.model_id == "future-model-display-name"
    with pytest.raises(CloudProviderConfigError, match="not an endpoint"):
        CloudProviderConfig(model_id="endpoint" + "://" + "not-allowed")


def test_validation_is_immutable_and_execution_denied() -> None:
    validation = validate_cloud_provider_config(CloudProviderConfig())
    assert validation.config_is_valid is True
    assert validation.execution_allowed is False
    assert validation.blockers == (
        "remote_http_not_allowed",
        "provider_not_built",
        "explicit_one_run_approval_required",
    )
    with pytest.raises(AttributeError):
        validation.execution_allowed = True  # type: ignore[misc]
    with pytest.raises(TypeError):
        CloudProviderConfigValidation(
            status=CloudProviderConfigStatus.DISABLED,
            execution_allowed=True,  # type: ignore[call-arg]
        )
