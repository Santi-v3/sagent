"""Disabled cloud-provider configuration metadata.

This module is an offline schema only. It does not read environment values,
resolve secrets, configure endpoints, build providers, mutate a ModelRouter,
or perform network or model calls.
"""

from dataclasses import dataclass, field
from enum import StrEnum

from sagent_agent_core.cloud_approval import (
    CLOUD_PROVIDER_IDS,
    CloudApprovalScope,
)
from sagent_agent_core.model_runtime import ModelTransport


class CloudProviderConfigError(ValueError):
    """Raised when disabled cloud configuration metadata violates the contract."""


class CloudProviderConfigStatus(StrEnum):
    """Non-executable states supported by the offline schema."""

    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"


class CloudSecretsSource(StrEnum):
    """Secret-source metadata; no value or reference name is stored or resolved."""

    ENV_REFERENCE_ONLY = "env_reference_only"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True, slots=True)
class CloudProviderConfig:
    """Immutable metadata for a future provider that is always disabled today."""

    provider_id: str = "deepseek-cloud"
    enabled: bool = False
    transport_kind: ModelTransport = ModelTransport.REMOTE_HTTP
    requires_explicit_approval: bool = True
    approval_scope: CloudApprovalScope = CloudApprovalScope.ONE_RUN_ONLY
    secrets_source: CloudSecretsSource = CloudSecretsSource.NOT_CONFIGURED
    model_id: str | None = None
    endpoint_configured: bool = False
    status: CloudProviderConfigStatus = CloudProviderConfigStatus.NOT_CONFIGURED

    def __post_init__(self) -> None:
        if self.provider_id not in CLOUD_PROVIDER_IDS:
            raise CloudProviderConfigError(
                f"Unknown or non-cloud provider: {self.provider_id}."
            )
        if self.enabled:
            raise CloudProviderConfigError(
                "Cloud provider configuration must remain disabled."
            )
        if self.transport_kind is not ModelTransport.REMOTE_HTTP:
            raise CloudProviderConfigError(
                "Cloud provider metadata must remain classified as remote_http."
            )
        if not self.requires_explicit_approval:
            raise CloudProviderConfigError(
                "Cloud provider configuration requires explicit per-run approval."
            )
        if self.approval_scope is not CloudApprovalScope.ONE_RUN_ONLY:
            raise CloudProviderConfigError(
                "Cloud provider approval scope must be one_run_only."
            )
        if not isinstance(self.secrets_source, CloudSecretsSource):
            raise CloudProviderConfigError(
                "Secrets source must be a supported metadata value."
            )
        if self.endpoint_configured:
            raise CloudProviderConfigError(
                "Endpoint configuration is not supported by the offline schema."
            )
        if not isinstance(self.status, CloudProviderConfigStatus):
            raise CloudProviderConfigError(
                "Status must be a disabled cloud configuration state."
            )

        expected_status = (
            CloudProviderConfigStatus.NOT_CONFIGURED
            if self.secrets_source is CloudSecretsSource.NOT_CONFIGURED
            else CloudProviderConfigStatus.DISABLED
        )
        if self.status is not expected_status:
            raise CloudProviderConfigError(
                "Status must be not_configured without a secret reference and disabled "
                "for env_reference_only metadata."
            )

        if self.model_id is not None:
            if (
                not self.model_id.strip()
                or len(self.model_id) > 128
                or any(character in self.model_id for character in "\r\n\0")
                or "://" in self.model_id
            ):
                raise CloudProviderConfigError(
                    "Model ID must be an optional bounded display label, not an endpoint."
                )


@dataclass(frozen=True, slots=True)
class CloudProviderConfigValidation:
    """Offline validation result that never grants execution authority."""

    status: CloudProviderConfigStatus
    config_is_valid: bool = field(default=True, init=False)
    execution_allowed: bool = field(default=False, init=False)
    blockers: tuple[str, ...] = field(
        default=(
            "remote_http_not_allowed",
            "provider_not_built",
            "explicit_one_run_approval_required",
        ),
        init=False,
    )


def validate_cloud_provider_config(
    config: CloudProviderConfig,
) -> CloudProviderConfigValidation:
    """Return deterministic disabled-state metadata without side effects."""

    return CloudProviderConfigValidation(
        status=config.status,
    )
