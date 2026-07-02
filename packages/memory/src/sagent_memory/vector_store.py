"""Provider-neutral vector-store contract with an offline deterministic fake."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from threading import Lock
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class VectorStoreError(ValueError):
    """Raised when a vector-store operation violates bounded local policy."""


@dataclass(frozen=True, slots=True)
class VectorPoint:
    point_id: str
    vector: tuple[float, ...]
    metadata: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.point_id or len(self.point_id) > 128:
            raise VectorStoreError("Vector point_id must be bounded.")
        if not 1 <= len(self.vector) <= 4_096:
            raise VectorStoreError("Vector dimension must be between 1 and 4096.")
        if not all(math.isfinite(value) for value in self.vector):
            raise VectorStoreError("Vector values must be finite.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class VectorSearchResult:
    point_id: str
    score: float


@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, point: VectorPoint) -> None: ...

    def query(
        self,
        vector: Sequence[float],
        *,
        limit: int,
        filters: Mapping[str, str] | None = None,
    ) -> tuple[VectorSearchResult, ...]: ...

    def delete(self, point_id: str) -> bool: ...


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


class InMemoryVectorStore:
    """Small deterministic fake for offline contract tests only."""

    def __init__(self, *, max_points: int = 1_000) -> None:
        if max_points < 1:
            raise VectorStoreError("max_points must be positive.")
        self._max_points = max_points
        self._dimension: int | None = None
        self._points: dict[str, VectorPoint] = {}
        self._lock = Lock()

    def upsert(self, point: VectorPoint) -> None:
        with self._lock:
            if self._dimension is None:
                self._dimension = len(point.vector)
            if len(point.vector) != self._dimension:
                raise VectorStoreError("Vector dimension does not match the store.")
            if point.point_id not in self._points and len(self._points) >= self._max_points:
                raise VectorStoreError("Vector point limit reached.")
            self._points[point.point_id] = point

    def query(
        self,
        vector: Sequence[float],
        *,
        limit: int,
        filters: Mapping[str, str] | None = None,
    ) -> tuple[VectorSearchResult, ...]:
        query = tuple(float(value) for value in vector)
        if not 1 <= limit <= 50:
            raise VectorStoreError("Vector query limit must be between 1 and 50.")
        if self._dimension is not None and len(query) != self._dimension:
            raise VectorStoreError("Query dimension does not match the store.")
        if not all(math.isfinite(value) for value in query):
            raise VectorStoreError("Query vector values must be finite.")
        required = dict(filters or {})
        with self._lock:
            points = tuple(self._points.values())
        results = [
            VectorSearchResult(point.point_id, _cosine(query, point.vector))
            for point in points
            if all(point.metadata.get(key) == value for key, value in required.items())
        ]
        results.sort(key=lambda item: (-item.score, item.point_id))
        return tuple(results[:limit])

    def delete(self, point_id: str) -> bool:
        with self._lock:
            return self._points.pop(point_id, None) is not None
