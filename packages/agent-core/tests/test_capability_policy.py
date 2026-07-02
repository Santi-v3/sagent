"""Tests for the offline capability/permission policy contract.

Every test runs without shell commands, git operations, network calls, model
invocations, file writes, secret access, or environment variable reads.
"""

import pytest

from sagent_agent_core.capability_policy import (
    DEFAULT_CAPABILITY_POLICY,
    CapabilityDecision,
    CapabilityMode,
    CapabilityName,
    CapabilityPolicy,
    CapabilityPolicyError,
    evaluate_capability,
)


class TestCapabilityPolicy:
    def test_default_policy_exists(self) -> None:
        """The default policy must contain all known capabilities."""
        for cap in CapabilityName:
            mode = DEFAULT_CAPABILITY_POLICY.get_mode(cap)
            assert isinstance(mode, CapabilityMode), f"{cap} missing from default policy"

    def test_default_policy_contains_expected_capabilities(self) -> None:
        caps = set(DEFAULT_CAPABILITY_POLICY.modes)
        expected = set(CapabilityName)
        assert caps == expected, f"Missing capabilities: {expected - caps}"

    def test_unknown_capability_defaults_to_disabled(self) -> None:
        policy = CapabilityPolicy()
        mode = policy.get_mode(CapabilityName.READ_WORKSPACE)
        assert mode is CapabilityMode.DISABLED

    def test_empty_policy_returns_disabled(self) -> None:
        policy = CapabilityPolicy()
        assert policy.get_mode(CapabilityName.READ_WORKSPACE) is CapabilityMode.DISABLED
        assert policy.get_mode(CapabilityName.PREVIEW_FILE_EDITS) is CapabilityMode.DISABLED

    def test_rejects_invalid_capability_name(self) -> None:
        with pytest.raises(CapabilityPolicyError, match="Invalid capability name"):
            CapabilityPolicy(modes={"not-a-capability": CapabilityMode.ALLOWED})  # type: ignore[arg-type]

    def test_rejects_invalid_mode(self) -> None:
        with pytest.raises(CapabilityPolicyError, match="Invalid mode"):
            CapabilityPolicy(modes={CapabilityName.READ_WORKSPACE: "invalid-mode"})  # type: ignore[arg-type]

    def test_policy_is_frozen(self) -> None:
        policy = CapabilityPolicy()
        with pytest.raises(AttributeError):
            policy.modes = {}  # type: ignore[misc]


class TestCapabilityModeDefaults:
    """Verify the approved default modes from the security contract."""

    def test_preview_file_edits_is_allowed(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.PREVIEW_FILE_EDITS)
        assert mode is CapabilityMode.ALLOWED

    def test_git_status_is_allowed(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.GIT_STATUS)
        assert mode is CapabilityMode.ALLOWED

    def test_apply_single_file_edit_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.APPLY_SINGLE_FILE_EDIT)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_apply_multi_file_edit_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.APPLY_MULTI_FILE_EDIT)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_run_tests_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.RUN_TESTS)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_run_shell_command_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.RUN_SHELL_COMMAND)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_git_commit_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.GIT_COMMIT)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_git_push_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.GIT_PUSH)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_change_dependencies_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.CHANGE_DEPENDENCIES)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_use_local_model_requires_approval(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.USE_LOCAL_MODEL)
        assert mode is CapabilityMode.APPROVAL_REQUIRED

    def test_use_cloud_model_is_disabled(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.USE_CLOUD_MODEL)
        assert mode is CapabilityMode.DISABLED

    def test_read_workspace_is_preview_only(self) -> None:
        mode = DEFAULT_CAPABILITY_POLICY.get_mode(CapabilityName.READ_WORKSPACE)
        assert mode is CapabilityMode.PREVIEW_ONLY


class TestEvaluateCapability:
    """evaluate_capability returns a decision without executing anything."""

    def test_allowed_capability_returns_allowed(self) -> None:
        policy = CapabilityPolicy(
            modes={CapabilityName.PREVIEW_FILE_EDITS: CapabilityMode.ALLOWED}
        )
        decision = evaluate_capability(policy, CapabilityName.PREVIEW_FILE_EDITS)
        assert decision is CapabilityDecision.ALLOWED

    def test_disabled_capability_returns_denied(self) -> None:
        policy = CapabilityPolicy(
            modes={CapabilityName.USE_CLOUD_MODEL: CapabilityMode.DISABLED}
        )
        decision = evaluate_capability(policy, CapabilityName.USE_CLOUD_MODEL)
        assert decision is CapabilityDecision.DENIED

    def test_approval_required_without_approval_returns_denied(self) -> None:
        policy = CapabilityPolicy(
            modes={CapabilityName.RUN_SHELL_COMMAND: CapabilityMode.APPROVAL_REQUIRED}
        )
        decision = evaluate_capability(
            policy, CapabilityName.RUN_SHELL_COMMAND, has_approval=False
        )
        assert decision is CapabilityDecision.DENIED

    def test_approval_required_with_approval_returns_needs_approval(self) -> None:
        policy = CapabilityPolicy(
            modes={CapabilityName.RUN_SHELL_COMMAND: CapabilityMode.APPROVAL_REQUIRED}
        )
        decision = evaluate_capability(
            policy, CapabilityName.RUN_SHELL_COMMAND, has_approval=True
        )
        assert decision is CapabilityDecision.NEEDS_APPROVAL

    def test_preview_only_returns_preview_only(self) -> None:
        policy = CapabilityPolicy(
            modes={CapabilityName.READ_WORKSPACE: CapabilityMode.PREVIEW_ONLY}
        )
        decision = evaluate_capability(policy, CapabilityName.READ_WORKSPACE)
        assert decision is CapabilityDecision.PREVIEW_ONLY

    def test_preview_only_with_is_preview_stays_preview_only(self) -> None:
        policy = CapabilityPolicy(
            modes={CapabilityName.READ_WORKSPACE: CapabilityMode.PREVIEW_ONLY}
        )
        decision = evaluate_capability(
            policy, CapabilityName.READ_WORKSPACE, is_preview=True
        )
        assert decision is CapabilityDecision.PREVIEW_ONLY

    def test_approval_required_with_is_preview_returns_preview_only(self) -> None:
        policy = CapabilityPolicy(
            modes={
                CapabilityName.APPLY_SINGLE_FILE_EDIT: CapabilityMode.APPROVAL_REQUIRED
            }
        )
        decision = evaluate_capability(
            policy, CapabilityName.APPLY_SINGLE_FILE_EDIT, is_preview=True
        )
        assert decision is CapabilityDecision.PREVIEW_ONLY

    def test_unknown_capability_returns_denied(self) -> None:
        policy = CapabilityPolicy()
        decision = evaluate_capability(policy, CapabilityName.RUN_SHELL_COMMAND)
        assert decision is CapabilityDecision.DENIED

    def test_default_policy_apply_single_file_edit_needs_approval(self) -> None:
        decision = evaluate_capability(
            DEFAULT_CAPABILITY_POLICY, CapabilityName.APPLY_SINGLE_FILE_EDIT
        )
        assert decision is CapabilityDecision.DENIED
        decision_with_approval = evaluate_capability(
            DEFAULT_CAPABILITY_POLICY, CapabilityName.APPLY_SINGLE_FILE_EDIT, has_approval=True
        )
        assert decision_with_approval is CapabilityDecision.NEEDS_APPROVAL

    def test_default_policy_use_cloud_model_is_denied(self) -> None:
        decision = evaluate_capability(
            DEFAULT_CAPABILITY_POLICY, CapabilityName.USE_CLOUD_MODEL
        )
        assert decision is CapabilityDecision.DENIED
        # Even with approval, cloud model remains disabled
        decision_with_approval = evaluate_capability(
            DEFAULT_CAPABILITY_POLICY, CapabilityName.USE_CLOUD_MODEL, has_approval=True
        )
        assert decision_with_approval is CapabilityDecision.DENIED


class TestDecisionDoesNotExecute:
    """Verification: evaluate_capability returns a data value, never a side effect."""

    def test_decision_is_pure_string(self) -> None:
        policy = DEFAULT_CAPABILITY_POLICY
        decision = evaluate_capability(policy, CapabilityName.PREVIEW_FILE_EDITS)
        assert isinstance(decision, CapabilityDecision)
        assert str(decision) == "allowed"

    def test_decision_does_not_contain_endpoints_or_urls(self) -> None:
        policy = DEFAULT_CAPABILITY_POLICY
        for cap in CapabilityName:
            decision = evaluate_capability(policy, cap)
            assert not hasattr(decision, "url")
            assert not hasattr(decision, "host")
            assert not hasattr(decision, "port")
            assert not hasattr(decision, "endpoint")
            assert not hasattr(decision, "api_key")
            assert not hasattr(decision, "secret")

    def test_decision_has_no_side_effects(self) -> None:
        """Calling evaluate_capability must not write, execute, or connect."""
        policy = DEFAULT_CAPABILITY_POLICY
        for cap in CapabilityName:
            decision = evaluate_capability(policy, cap)
            # A decision is a frozen StrEnum; it cannot reference executors.
            assert isinstance(decision, CapabilityDecision)
            assert not hasattr(decision, "executor")
            assert not hasattr(decision, "adapter")
            assert not hasattr(decision, "router")
            assert not hasattr(decision, "transport")

    def test_decision_cannot_activate_capability(self) -> None:
        """Decisions must not contain callable references or executors."""
        decision = evaluate_capability(
            DEFAULT_CAPABILITY_POLICY, CapabilityName.RUN_SHELL_COMMAND
        )
        assert not callable(getattr(decision, "run", None))
        assert not hasattr(decision, "subprocess")
        assert not hasattr(decision, "shell")
        assert not hasattr(decision, "execute")

    def test_model_response_gets_no_tool_authority(self) -> None:
        """A model response could never produce a policy decision with authority."""
        policy = DEFAULT_CAPABILITY_POLICY
        for cap in CapabilityName:
            decision = evaluate_capability(policy, cap)
            # Decisions are StrEnum values with no input or tool slots.
            assert not hasattr(decision, "model_response")
            assert not hasattr(decision, "tool_call")
            assert not hasattr(decision, "authority")


class TestPolicyHasNoSecretsOrEnvAccess:
    """The CapabilityPolicy contract reads no secrets, env vars, or files."""

    def test_policy_contains_no_secrets(self) -> None:
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "api_key")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "secret")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "token")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "password")

    def test_policy_contains_no_endpoints_or_ports(self) -> None:
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "url")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "host")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "port")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "endpoint")

    def test_policy_contains_no_env_references(self) -> None:
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "env")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "environment")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "SAGENT")

    def test_policy_has_no_model_runtime_references(self) -> None:
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "adapter")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "router")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "transport")

    def test_policy_has_no_provider_references(self) -> None:
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "provider")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "deepseek")
        assert not hasattr(DEFAULT_CAPABILITY_POLICY, "remote_http")


class TestCustomPolicy:
    """Users can override the default policy with custom modes."""

    def test_custom_policy_overrides_default_mode(self) -> None:
        custom = CapabilityPolicy(
            modes={CapabilityName.READ_WORKSPACE: CapabilityMode.ALLOWED}
        )
        assert custom.get_mode(CapabilityName.READ_WORKSPACE) is CapabilityMode.ALLOWED
        # Unknown capabilities still default to disabled
        assert custom.get_mode(CapabilityName.GIT_STATUS) is CapabilityMode.DISABLED

    def test_custom_policy_evaluation(self) -> None:
        custom = CapabilityPolicy(
            modes={CapabilityName.RUN_SHELL_COMMAND: CapabilityMode.ALLOWED}
        )
        decision = evaluate_capability(custom, CapabilityName.RUN_SHELL_COMMAND)
        assert decision is CapabilityDecision.ALLOWED
