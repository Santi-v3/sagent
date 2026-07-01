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
