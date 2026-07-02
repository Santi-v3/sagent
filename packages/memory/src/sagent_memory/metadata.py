"""Typed metadata for the Memory V2 domains named in the master plan."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class MemoryMetadataError(ValueError):
    """Raised when structured memory metadata is outside the public contract."""


class MemoryKind(StrEnum):
    PROJECT_KNOWLEDGE = "project_knowledge"
    DECISION = "decision"
    TASK_HISTORY = "task_history"
    SUMMARY = "summary"


class MemorySource(StrEnum):
    USER_APPROVED = "user_approved"
    WORKSPACE = "workspace"
    TASK = "task"
    SUMMARY = "summary"


class MemoryStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class MemoryRecordMetadata:
    kind: MemoryKind
    source: MemorySource
    status: MemoryStatus = MemoryStatus.ACTIVE
    project_id: str | None = None

    def __post_init__(self) -> None:
        if self.project_id is not None and not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", self.project_id
        ):
            raise MemoryMetadataError("project_id must be a bounded identifier.")

    def as_mapping(self) -> Mapping[str, str]:
        values = {
            "kind": self.kind.value,
            "source": self.source.value,
            "status": self.status.value,
        }
        if self.project_id is not None:
            values["project_id"] = self.project_id
        return MappingProxyType(values)
