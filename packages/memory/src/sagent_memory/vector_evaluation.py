"""Deterministic synthetic harness for provider-neutral vector-store adapters."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sagent_memory.vector_store import VectorPoint, VectorStore


@dataclass(frozen=True, slots=True)
class VectorEvaluationReport:
    adapter_id: str
    checks: Mapping[str, bool]
    passed: bool
    synthetic_only: bool = True
    network_used: bool = False
    model_called: bool = False


VectorStoreFactory = Callable[[], VectorStore]


SYNTHETIC_POINTS = (
    VectorPoint("decision-a", (1.0, 0.0, 0.0), {"kind": "decision", "project_id": "a"}),
    VectorPoint("task-a", (0.0, 1.0, 0.0), {"kind": "task_history", "project_id": "a"}),
    VectorPoint("decision-b", (0.8, 0.2, 0.0), {"kind": "decision", "project_id": "b"}),
)


def evaluate_vector_store(adapter_id: str, factory: VectorStoreFactory) -> VectorEvaluationReport:
    if not adapter_id or len(adapter_id) > 64:
        raise ValueError("adapter_id must be bounded.")
    store = factory()
    for point in SYNTHETIC_POINTS:
        store.upsert(point)

    nearest = store.query((1.0, 0.0, 0.0), limit=3)
    filtered = store.query(
        (1.0, 0.0, 0.0),
        limit=3,
        filters={"kind": "decision", "project_id": "b"},
    )
    deleted = store.delete("decision-a")
    after_delete = store.query(
        (1.0, 0.0, 0.0),
        limit=3,
        filters={"kind": "decision", "project_id": "a"},
    )
    checks = {
        "nearest_neighbor": bool(nearest and nearest[0].point_id == "decision-a"),
        "metadata_filter": bool(len(filtered) == 1 and filtered[0].point_id == "decision-b"),
        "delete_acknowledged": deleted,
        "deleted_point_absent": not after_delete,
        "bounded_results": len(nearest) <= 3,
    }
    return VectorEvaluationReport(
        adapter_id=adapter_id,
        checks=MappingProxyType(checks),
        passed=all(checks.values()),
    )
