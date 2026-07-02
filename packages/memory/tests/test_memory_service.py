from dataclasses import FrozenInstanceError

import pytest
from sagent_memory import MemoryApprovalRequiredError, MemoryService


def test_default_memory_is_offline_and_requires_confirmation(tmp_path) -> None:
    service = MemoryService()

    with pytest.raises(MemoryApprovalRequiredError):
        service.store("Do not write")

    assert service.list_entries() == ()
    assert list(tmp_path.iterdir()) == []


def test_confirmed_memory_can_be_searched_without_embeddings() -> None:
    service = MemoryService()
    entry = service.store(
        "Sagent requires exact approval hashes",
        {"kind": "decision"},
        confirmed=True,
    )

    results = service.search("approval hashes")

    assert results[0][0] == entry
    assert results[0][1] > 0
    assert dict(entry.metadata) == {"kind": "decision"}
    with pytest.raises(FrozenInstanceError):
        entry.text = "changed"  # type: ignore[misc]


def test_embedding_function_is_injected_not_built_in() -> None:
    calls: list[str] = []

    def embed(text: str) -> tuple[float, float]:
        calls.append(text)
        return (1.0, 0.0) if "approval" in text else (0.0, 1.0)

    service = MemoryService(embedding_function=embed)
    service.store("approval policy", confirmed=True)
    service.store("visual layout", confirmed=True)

    results = service.search("approval")

    assert results[0][0].text == "approval policy"
    assert calls == ["approval policy", "visual layout", "approval"]


def test_sqlite_persistence_is_explicit_and_local(tmp_path) -> None:
    database = tmp_path / "memory.sqlite3"
    first = MemoryService(database_path=database)
    entry = first.store("persistent local note", confirmed=True)

    second = MemoryService(database_path=database)

    assert second.list_entries()[0].entry_id == entry.entry_id
    assert second.delete(entry.entry_id, confirmed=True) is True
    assert MemoryService(database_path=database).list_entries() == ()


def test_delete_requires_confirmation() -> None:
    service = MemoryService()
    entry = service.store("keep me", confirmed=True)

    with pytest.raises(MemoryApprovalRequiredError):
        service.delete(entry.entry_id)

    assert service.list_entries() == (entry,)


def test_punctuation_only_search_is_safe_and_deterministic() -> None:
    service = MemoryService()
    service.store("...", confirmed=True)

    assert service.search("???") == ()
