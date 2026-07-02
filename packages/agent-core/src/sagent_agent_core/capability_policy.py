"""Capability/Permission policy — offline contract for controlled capability gating.

This module defines what Sagent *may* do, not how. It does not execute shell
commands, git operations, network calls, model invocations, or file writes.
It only evaluates capability requests against a policy and returns a decision.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final


class CapabilityPolicyError(ValueError):
    """Raised when a capability policy or evaluation is misconfigured."""


class CapabilityName(StrEnum):
    """Named capabilities that Sagent can be granted or denied."""

    READ_WORKSPACE = "read_workspace"
    PREVIEW_FILE_EDITS = "preview_file_edits"
    APPLY_SINGLE_FILE_EDIT = "apply_single_file_edit"
    APPLY_MULTI_FILE_EDIT = "apply_multi_file_edit"
    RUN_TESTS = "run_tests"
    RUN_SHELL_COMMAND = "run_shell_command"
    GIT_STATUS = "git_status"
    GIT_COMMIT = "git_commit"
    GIT_PUSH = "git_push"
    CHANGE_DEPENDENCIES = "change_dependencies"
    USE_LOCAL_MODEL = "use_local_model"
    USE_CLOUD_MODEL = "use_cloud_model"


class CapabilityMode(StrEnum):
    """Level of restriction for a named capability."""

    DISABLED = "disabled"
    PREVIEW_ONLY = "preview_only"
    APPROVAL_REQUIRED = "approval_required"
    ALLOWED = "allowed"


class CapabilityDecision(StrEnum):
    """Result of evaluating a capability against a policy.

    A decision never activates a capability — it only reports what the
    caller is permitted to do next.
    """

    ALLOWED = "allowed"
    NEEDS_APPROVAL = "needs_approval"
    PREVIEW_ONLY = "preview_only"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class CapabilityPolicy:
    """Immutable mapping from CapabilityName to CapabilityMode.

    Constructing a policy validates modes but does not grant, execute, or
    activate any capability.
    """

    modes: dict[CapabilityName, CapabilityMode] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for cap, mode in self.modes.items():
            if not isinstance(cap, CapabilityName):
                raise CapabilityPolicyError(f"Invalid capability name: {cap}")
            if not isinstance(mode, CapabilityMode):
                raise CapabilityPolicyError(f"Invalid mode for {cap}: {mode}")

    def get_mode(self, capability: CapabilityName) -> CapabilityMode:
        """Return the mode for *capability*, or DISABLED if unknown."""
        return self.modes.get(capability, CapabilityMode.DISABLED)


def evaluate_capability(
    policy: CapabilityPolicy,
    capability: CapabilityName,
    has_approval: bool = False,
    is_preview: bool = False,
) -> CapabilityDecision:
    """Evaluate whether a capability request is granted under the given policy.

    This is a pure offline decision: no shell, git, network, model, or file
    access occurs. The caller must enforce the returned decision.

    Args:
        policy: the capability policy to evaluate against.
        capability: the capability being requested.
        has_approval: whether the caller already holds a valid approval
                      for this request.
        is_preview: whether the caller is requesting a preview (read-only
                    inspection) rather than execution.

    Returns:
        CapabilityDecision — one of ALLOWED, NEEDS_APPROVAL, PREVIEW_ONLY,
        or DENIED.
    """
    mode = policy.get_mode(capability)

    if mode is CapabilityMode.ALLOWED:
        return CapabilityDecision.ALLOWED
    if mode is CapabilityMode.DISABLED:
        return CapabilityDecision.DENIED
    if is_preview and mode in (CapabilityMode.PREVIEW_ONLY, CapabilityMode.APPROVAL_REQUIRED):
        return CapabilityDecision.PREVIEW_ONLY
    if mode is CapabilityMode.PREVIEW_ONLY:
        return CapabilityDecision.PREVIEW_ONLY
    if mode is CapabilityMode.APPROVAL_REQUIRED:
        return CapabilityDecision.NEEDS_APPROVAL if has_approval else CapabilityDecision.DENIED

    return CapabilityDecision.DENIED


DEFAULT_CAPABILITY_POLICY: Final[CapabilityPolicy] = CapabilityPolicy(
    modes={
        CapabilityName.READ_WORKSPACE: CapabilityMode.PREVIEW_ONLY,
        CapabilityName.PREVIEW_FILE_EDITS: CapabilityMode.ALLOWED,
        CapabilityName.APPLY_SINGLE_FILE_EDIT: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.APPLY_MULTI_FILE_EDIT: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.RUN_TESTS: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.RUN_SHELL_COMMAND: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.GIT_STATUS: CapabilityMode.ALLOWED,
        CapabilityName.GIT_COMMIT: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.GIT_PUSH: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.CHANGE_DEPENDENCIES: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.USE_LOCAL_MODEL: CapabilityMode.APPROVAL_REQUIRED,
        CapabilityName.USE_CLOUD_MODEL: CapabilityMode.DISABLED,
    },
)
