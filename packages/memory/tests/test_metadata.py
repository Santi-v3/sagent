from dataclasses import FrozenInstanceError

import pytest
from sagent_memory import (
    MemoryContractError,
    MemoryKind,
    MemoryMetadataError,
    MemoryRecordMetadata,
    MemoryService,
    MemorySource,
    MemoryStatus,
)


def test_masterplan_memory_domains_are_fixed_and_public() -> None:
    assert tuple(item.value for item in MemoryKind) == (
        "project_knowledge",
        "decision",
        "task_history",
        "summary",
    )


def test_record_metadata_is_frozen_and_serializable() -> None:
    metadata = MemoryRecordMetadata(
        MemoryKind.DECISION,
        MemorySource.USER_APPROVED,
        project_id="sagent",
    )

    assert dict(metadata.as_mapping()) == {
        "kind": "decision",
        "source": "user_approved",
        "status": "active",
        "project_id": "sagent",
    }
    with pytest.raises(FrozenInstanceError):
        metadata.status = MemoryStatus.ARCHIVED  # type: ignore[misc]


def test_project_id_is_bounded() -> None:
    with pytest.raises(MemoryMetadataError):
        MemoryRecordMetadata(
            MemoryKind.PROJECT_KNOWLEDGE,
            MemorySource.WORKSPACE,
            project_id="../outside",
        )


def test_unknown_structured_metadata_values_are_rejected() -> None:
    service = MemoryService()

    with pytest.raises(MemoryContractError, match="unknown"):
        service.store("note", {"kind": "arbitrary"}, confirmed=True)


def test_list_and_search_filter_by_typed_metadata() -> None:
    service = MemoryService()
    decision = MemoryRecordMetadata(MemoryKind.DECISION, MemorySource.USER_APPROVED)
    task = MemoryRecordMetadata(MemoryKind.TASK_HISTORY, MemorySource.TASK)
    service.store("approval decision", decision.as_mapping(), confirmed=True)
    service.store("approval task", task.as_mapping(), confirmed=True)

    listed = service.list_entries(kind=MemoryKind.DECISION)
    searched = service.search("approval", kind=MemoryKind.TASK_HISTORY)

    assert [entry.metadata["kind"] for entry in listed] == ["decision"]
    assert [entry.metadata["kind"] for entry, _score in searched] == ["task_history"]
