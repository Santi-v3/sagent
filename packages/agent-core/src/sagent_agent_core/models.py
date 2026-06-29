"""Immutable domain models for prepared and approved file changes."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ChangeOperation(StrEnum):
    """Supported file mutations in MVP 1.C."""

    CREATE = "create"
    UPDATE = "update"


class ChangeSetStatus(StrEnum):
    """Lifecycle of an exact, content-bound set of changes."""

    PREPARED = "prepared"
    APPROVED = "approved"
    APPLIED = "applied"


@dataclass(frozen=True, slots=True)
class ChangeRequest:
    """One requested text-file change before workspace inspection."""

    path: str
    new_content: str
    operation: ChangeOperation


@dataclass(frozen=True, slots=True)
class FileChange:
    """One inspected change with its before state and visible diff."""

    path: str
    operation: ChangeOperation
    old_content: str | None
    new_content: str
    old_sha256: str | None
    new_sha256: str
    diff: str


@dataclass(frozen=True, slots=True)
class ChangeSet:
    """A proposal whose hash binds approval to exact paths and contents."""

    change_set_id: UUID
    changes: tuple[FileChange, ...]
    proposal_hash: str
    status: ChangeSetStatus
    created_at: datetime
    approved_at: datetime | None = None
    applied_at: datetime | None = None
