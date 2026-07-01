"""Tests for the offline cloud approval contract.

Every test runs without network, without model calls, and without accessing
any API key, secret, or endpoint configuration.
"""

import pytest

from sagent_agent_core.cloud_approval import (
    CLOUD_PROVIDER_IDS,
    CloudApprovalDecision,
    CloudApprovalError,
    CloudApprovalRequest,
    CloudApprovalScope,
    CloudDataDisclosure,
    CloudPurpose,
    is_cloud_approval_valid,
)


def _make_request(**kwargs: object) -> CloudApprovalRequest:
    """Helper to construct a CloudApprovalRequest, then run __post_init__ for validation."""
    import dataclasses

    field_defaults = {f.name: f.default for f in dataclasses.fields(CloudApprovalRequest)}
    field_defaults.update(kwargs)
    inst = object.__new__(CloudApprovalRequest)
    for name, val in field_defaults.items():
        object.__setattr__(inst, name, val)
    type(inst).__post_init__(inst)
    return inst


def _unstripped_decision(**kwargs: object) -> CloudApprovalDecision:
    """Helper to construct a CloudApprovalDecision WITHOUT __post_init__ validation."""
    import dataclasses

    field_defaults = {f.name: f.default for f in dataclasses.fields(CloudApprovalDecision)}
    field_defaults.update(kwargs)
    inst = object.__new__(CloudApprovalDecision)
    for name, val in field_defaults.items():
        object.__setattr__(inst, name, val)
    return inst


def _unstripped_request(**kwargs: object) -> CloudApprovalRequest:
    """Helper to construct a CloudApprovalRequest WITHOUT __post_init__ validation."""
    import dataclasses

    field_defaults = {f.name: f.default for f in dataclasses.fields(CloudApprovalRequest)}
    field_defaults.update(kwargs)
    inst = object.__new__(CloudApprovalRequest)
    for name, val in field_defaults.items():
        object.__setattr__(inst, name, val)
    return inst


class TestCloudDataDisclosure:
    def test_default_deny_secrets(self) -> None:
        """secrets_excluded must be True by default and cannot be False."""
        d = CloudDataDisclosure()
        assert d.secrets_excluded is True

    def test_rejects_secrets_included(self) -> None:
        with pytest.raises(CloudApprovalError, match="Secrets"):
            CloudDataDisclosure(secrets_excluded=False)

    def test_rejects_full_repo_dump(self) -> None:
        with pytest.raises(CloudApprovalError, match="Full repository dumps"):
            CloudDataDisclosure(full_repo_dump=True)

    def test_rejects_negative_bytes(self) -> None:
        with pytest.raises(CloudApprovalError, match="non-negative"):
            CloudDataDisclosure(bytes_estimate=-1)

    def test_zero_bytes_is_valid(self) -> None:
        d = CloudDataDisclosure(bytes_estimate=0)
        assert d.bytes_estimate == 0


class TestCloudApprovalRequest:
    def test_default_denied_contract(self) -> None:
        """A default request must specify a known cloud provider and scope."""
        r = CloudApprovalRequest()
        assert r.provider_id == "deepseek-cloud"
        assert r.scope is CloudApprovalScope.ONE_RUN_ONLY
        assert r.purpose is CloudPurpose.CODING

    def test_unknown_provider_rejected(self) -> None:
        with pytest.raises(CloudApprovalError, match="Unknown"):
            CloudApprovalRequest(provider_id="unknown-provider")

    def test_local_provider_not_allowed(self) -> None:
        for pid in ("lm-studio", "ollama", "openai"):
            with pytest.raises(CloudApprovalError, match="Unknown"):
                CloudApprovalRequest(provider_id=pid)

    def test_non_one_run_only_scope_rejected(self) -> None:
        with pytest.raises(CloudApprovalError, match="one_run_only"):
            _make_request(scope="repeating")

    def test_invalid_purpose_rejected(self) -> None:
        with pytest.raises(CloudApprovalError, match="Purpose"):
            CloudApprovalRequest(purpose="invalid-purpose")  # type: ignore[arg-type]


class TestCloudApprovalDecision:
    def test_default_denied(self) -> None:
        """Default decision must be denied (approved=False)."""
        d = CloudApprovalDecision()
        assert d.approved is False
        assert d.explicit_confirmed is False

    def test_requires_explicit_confirmation(self) -> None:
        req = CloudApprovalRequest()
        with pytest.raises(CloudApprovalError, match="explicit_confirmed"):
            CloudApprovalDecision(approved=True, explicit_confirmed=False, request=req)

    def test_requires_request_when_approved(self) -> None:
        with pytest.raises(CloudApprovalError, match="CloudApprovalRequest"):
            CloudApprovalDecision(approved=True, explicit_confirmed=True, request=None)

    def test_explicit_confirmed_requires_approved(self) -> None:
        with pytest.raises(CloudApprovalError, match="explicit_confirmed.*approved"):
            CloudApprovalDecision(approved=False, explicit_confirmed=True)

    def test_valid_approval(self) -> None:
        req = CloudApprovalRequest()
        d = CloudApprovalDecision(
            approved=True,
            explicit_confirmed=True,
            request=req,
        )
        assert d.approved is True
        assert d.explicit_confirmed is True
        assert d.request is req
        assert d.decided_at is not None


class TestIsCloudApprovalValid:
    def test_default_decision_invalid(self) -> None:
        assert is_cloud_approval_valid(CloudApprovalDecision()) is False

    def test_not_approved_invalid(self) -> None:
        d = CloudApprovalDecision(approved=False)
        assert is_cloud_approval_valid(d) is False

    def test_not_explicitly_confirmed_invalid(self) -> None:
        d = _unstripped_decision(
            approved=True,
            explicit_confirmed=False,
            request=CloudApprovalRequest(),
        )
        assert is_cloud_approval_valid(d) is False

    def test_no_request_invalid(self) -> None:
        d = _unstripped_decision(
            approved=True,
            explicit_confirmed=True,
            request=None,
        )
        assert is_cloud_approval_valid(d) is False

    def test_valid_returns_true(self) -> None:
        req = CloudApprovalRequest()
        d = CloudApprovalDecision(
            approved=True,
            explicit_confirmed=True,
            request=req,
        )
        assert is_cloud_approval_valid(d) is True

    def test_unknown_provider_invalid(self) -> None:
        req = _unstripped_request(provider_id="unknown")
        d = _unstripped_decision(
            approved=True,
            explicit_confirmed=True,
            request=req,
        )
        assert is_cloud_approval_valid(d) is False


class TestCloudProviderIds:
    def test_known_providers(self) -> None:
        assert "deepseek-cloud" in CLOUD_PROVIDER_IDS

    def test_no_local_providers_in_cloud_set(self) -> None:
        for local in ("lm-studio", "ollama", "openai"):
            assert local not in CLOUD_PROVIDER_IDS

    def test_frozen_set(self) -> None:
        with pytest.raises(AttributeError):
            CLOUD_PROVIDER_IDS.add("new-provider")  # type: ignore[attr-defined]


class TestApprovalDoesNotActivateRemoteHttp:
    """Verification: approval is a local data record, not a remote invocation."""

    def test_decision_is_frozen_data(self) -> None:
        d = CloudApprovalDecision()
        with pytest.raises(AttributeError):
            d.approved = True  # type: ignore[misc]

    def test_request_has_no_transport(self) -> None:
        req = CloudApprovalRequest()
        assert not hasattr(req, "transport")
        assert not hasattr(req, "endpoint")
        assert not hasattr(req, "api_key")

    def test_disclosure_makes_no_network_claims(self) -> None:
        d = CloudDataDisclosure()
        assert not hasattr(d, "url")
        assert not hasattr(d, "host")
        assert not hasattr(d, "port")
        assert not hasattr(d, "endpoint")
