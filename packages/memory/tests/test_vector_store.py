from dataclasses import FrozenInstanceError

import pytest
from sagent_memory import (
    InMemoryVectorStore,
    MemoryKind,
    MemoryRecordMetadata,
    MemoryService,
    MemorySource,
    VectorPoint,
    VectorStoreError,
)


def test_in_memory_vector_store_is_bounded_deterministic_and_filterable() -> None:
    store = InMemoryVectorStore(max_points=2)
    store.upsert(VectorPoint("a", (1.0, 0.0), {"kind": "decision"}))
    store.upsert(VectorPoint("b", (0.0, 1.0), {"kind": "task_history"}))

    results = store.query((1.0, 0.0), limit=2, filters={"kind": "decision"})

    assert [(result.point_id, result.score) for result in results] == [("a", 1.0)]
    with pytest.raises(VectorStoreError, match="limit"):
        store.upsert(VectorPoint("c", (1.0, 1.0), {}))


def test_vector_dimension_and_non_finite_values_are_rejected() -> None:
    store = InMemoryVectorStore()
    store.upsert(VectorPoint("a", (1.0, 0.0), {}))

    with pytest.raises(VectorStoreError, match="dimension"):
        store.upsert(VectorPoint("b", (1.0,), {}))
    with pytest.raises(VectorStoreError, match="finite"):
        VectorPoint("bad", (float("nan"),), {})


def test_vector_point_is_deeply_immutable_at_metadata_boundary() -> None:
    point = VectorPoint("a", (1.0,), {"kind": "decision"})

    with pytest.raises(TypeError):
        point.metadata["kind"] = "task_history"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        point.point_id = "b"  # type: ignore[misc]


def test_memory_service_uses_injected_store_without_network_or_provider() -> None:
    def embed(text: str) -> tuple[float, float]:
        return (1.0, 0.0) if "decision" in text else (0.0, 1.0)

    vectors = InMemoryVectorStore()
    memory = MemoryService(embedding_function=embed, vector_store=vectors)
    decision = MemoryRecordMetadata(MemoryKind.DECISION, MemorySource.USER_APPROVED)
    task = MemoryRecordMetadata(MemoryKind.TASK_HISTORY, MemorySource.TASK)
    decision_entry = memory.store("decision record", decision.as_mapping(), confirmed=True)
    memory.store("task record", task.as_mapping(), confirmed=True)

    results = memory.search("decision", kind=MemoryKind.DECISION)

    assert results[0][0] == decision_entry
    assert results[0][1] == 1.0
    assert memory.delete(decision_entry.entry_id, confirmed=True) is True
    assert vectors.query((1.0, 0.0), limit=5, filters={"kind": "decision"}) == ()


def test_vector_store_protocol_has_no_endpoint_or_network_configuration() -> None:
    store = InMemoryVectorStore()

    assert not hasattr(store, "url")
    assert not hasattr(store, "endpoint")
    assert not hasattr(store, "api_key")
