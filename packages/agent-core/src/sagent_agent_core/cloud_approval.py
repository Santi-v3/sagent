"""Offline cloud approval contract — pure data structures and validation rules.

No network, no model call, no remote_http activation, no file access, and no
API key or secret handling. This module documents the approval gates that a
later cloud integration must pass; it does not implement any cloud provider.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Final
from uuid import UUID, uuid4


class CloudApprovalError(ValueError):
    """Raised when a cloud approval request or decision is invalid."""


class CloudPurpose(StrEnum):
    """Approved task classes for a potential future cloud provider."""

    CODING = "coding"
    ARCHITECTURE = "architecture"
    DEBUGGING = "debugging"


class CloudApprovalScope(StrEnum):
    """Scope of a single cloud approval — currently only one_run_only."""

    ONE_RUN_ONLY = "one_run_only"


# Known future cloud provider identities. These are the only provider IDs a
# later cloud-approval flow may reference. None of them are currently
# buildable or executable.
CLOUD_PROVIDER_IDS: Final[frozenset[str]] = frozenset({"deepseek-cloud"})


@dataclass(frozen=True, slots=True)
class CloudDataDisclosure:
    """Declared data fields the cloud run would transfer.

    This is a *declaration* shown to the user before approval. No data is
    actually read, collected, or transmitted by constructing this record.
    """

    repo_context_included: bool = False
    diffs_included: bool = False
    files_included: bool = False
    data_was_redacted: bool = False
    secrets_excluded: bool = True
    full_repo_dump: bool = False
    bytes_estimate: int = 0

    def __post_init__(self) -> None:
        if not self.secrets_excluded:
            raise CloudApprovalError(
                "Secrets, API keys, tokens, and .env contents must always be excluded."
            )
        if self.full_repo_dump:
            raise CloudApprovalError(
                "Full repository dumps are never allowed for cloud processing."
            )
        if self.bytes_estimate < 0:
            raise CloudApprovalError("Byte estimate must be non-negative.")


@dataclass(frozen=True, slots=True)
class CloudApprovalRequest:
    """One immutable approval request shown to the user for confirmation.

    Constructing this request validates structural rules but does not
    grant access, activate any provider, or transmit any data.
    """

    approval_id: UUID = field(default_factory=uuid4)
    provider_id: str = "deepseek-cloud"
    purpose: CloudPurpose = CloudPurpose.CODING
    disclosure: CloudDataDisclosure = field(default_factory=CloudDataDisclosure)
    scope: CloudApprovalScope = CloudApprovalScope.ONE_RUN_ONLY

    def __post_init__(self) -> None:
        if self.provider_id not in CLOUD_PROVIDER_IDS:
            raise CloudApprovalError(
                f"Unknown or non-cloud provider: {self.provider_id}. "
                f"Allowed cloud provider IDs: {sorted(CLOUD_PROVIDER_IDS)}."
            )
        if not isinstance(self.purpose, CloudPurpose):
            raise CloudApprovalError("Purpose must be a valid CloudPurpose enum value.")
        if self.scope is not CloudApprovalScope.ONE_RUN_ONLY:
            raise CloudApprovalError(
                "Cloud approval scope must be one_run_only. "
                "Repeated, background, or timed cloud calls are not allowed."
            )


@dataclass(frozen=True, slots=True)
class CloudApprovalDecision:
    """The result of a user confirming or denying a cloud run.

    A decision never activates a provider, opens a network connection,
    reads files, or transmits data. It is only a local record that a
    user did (or did not) consent to an exact, previously displayed
    CloudApprovalRequest.
    """

    approved: bool = False
    explicit_confirmed: bool = False
    request: CloudApprovalRequest | None = None
    decided_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))  # noqa: UP017

    def __post_init__(self) -> None:
        if self.approved and not self.explicit_confirmed:
            raise CloudApprovalError(
                "Cloud approval requires explicit_confirmed=True. "
                "Default confirmation, implicit acceptance, or inferred "
                "consent is not sufficient."
            )
        if self.approved and self.request is None:
            raise CloudApprovalError(
                "An approved CloudApprovalDecision must reference the exact "
                "CloudApprovalRequest the user confirmed."
            )
        if self.explicit_confirmed and not self.approved:
            raise CloudApprovalError(
                "explicit_confirmed=True requires approved=True. "
                "A user who confirms must be recorded as approving."
            )


def is_cloud_approval_valid(decision: CloudApprovalDecision) -> bool:
    """Return True only when a fully valid cloud approval is in place.

    This is an offline check: it validates contract rules without
    activating any network, provider, or file access.
    """
    if not decision.approved:
        return False
    if not decision.explicit_confirmed:
        return False
    if decision.request is None:
        return False
    if decision.request.scope is not CloudApprovalScope.ONE_RUN_ONLY:
        return False
    if decision.request.provider_id not in CLOUD_PROVIDER_IDS:
        return False
    return True


@dataclass(frozen=True, slots=True)
class CloudApprovalPreview:
    """Offline preview of a cloud approval request and its current decision status.

    This is a pure data transformation of CloudApprovalRequest and
    CloudApprovalDecision into a user-facing summary. It does not read files,
    make network calls, build providers, or activate remote_http.
    """

    provider_id: str
    purpose: str
    scope: str
    explicit_confirmed: bool
    is_approved: bool

    repo_context_included: bool
    diffs_included: bool
    files_included: bool
    data_was_redacted: bool
    secrets_excluded: bool
    full_repo_dump_blocked: bool
    bytes_estimate: int

    approval_status: str
    is_valid: bool
    risk_hints: tuple[str, ...]


def build_cloud_approval_preview(
    request: CloudApprovalRequest,
    decision: CloudApprovalDecision | None = None,
) -> CloudApprovalPreview:
    """Build an offline preview from a CloudApprovalRequest and optional decision.

    Args:
        request: the immutable approval request.
        decision: an optional decision; if None the preview shows
                  'no_decision'.

    Returns:
        A CloudApprovalPreview containing only metadata from the contract.
        No files, network, endpoints, API keys, or provider objects are
        touched.
    """
    if decision is not None and decision.request is not None and decision.request is not request:
        raise CloudApprovalError(
            "The decision's request must match the provided request argument."
        )

    approved = decision is not None and decision.approved
    explicit_confirmed = decision is not None and decision.explicit_confirmed

    if decision is not None:
        valid = is_cloud_approval_valid(decision)
        status = "approved" if valid else "denied"
    else:
        valid = False
        status = "no_decision"

    hints: list[str] = []
    hints.append("cloud processing means external data transfer")
    if request.disclosure.repo_context_included:
        hints.append("repository context included")
    if request.disclosure.diffs_included:
        hints.append("diffs included")
    if request.disclosure.files_included:
        hints.append("specific files included")
    if not request.disclosure.secrets_excluded:
        hints.append("secrets are NOT excluded")
    if request.disclosure.full_repo_dump:
        hints.append("full repository dump included")

    return CloudApprovalPreview(
        provider_id=request.provider_id,
        purpose=str(request.purpose),
        scope=str(request.scope),
        explicit_confirmed=explicit_confirmed,
        is_approved=approved,
        repo_context_included=request.disclosure.repo_context_included,
        diffs_included=request.disclosure.diffs_included,
        files_included=request.disclosure.files_included,
        data_was_redacted=request.disclosure.data_was_redacted,
        secrets_excluded=request.disclosure.secrets_excluded,
        full_repo_dump_blocked=not request.disclosure.full_repo_dump,
        bytes_estimate=request.disclosure.bytes_estimate,
        approval_status=status,
        is_valid=valid,
        risk_hints=tuple(hints),
    )
