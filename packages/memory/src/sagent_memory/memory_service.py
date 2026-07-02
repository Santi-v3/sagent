"""Bounded local memory with no implicit model or network access."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from uuid import uuid4


class MemoryContractError(ValueError):
    """Raised when a memory operation violates the local contract."""


class MemoryApprovalRequiredError(PermissionError):
    """Raised when a mutating memory operation lacks confirmation."""


EmbeddingFunction = Callable[[str], Sequence[float] | None]
MetadataValue = str | int | float | bool


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    entry_id: str
    text: str
    metadata: Mapping[str, MetadataValue]
    embedding: tuple[float, ...] | None = None


def _tokens(text: str) -> frozenset[str]:
    return frozenset(re.findall(r"[a-z0-9äöüß_-]+", text.casefold()))


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


class MemoryService:
    """Store and search explicitly confirmed local memory entries.

    The default service is process-local. Persistence and embeddings are only
    enabled when the caller injects a database path or embedding function.
    This module never reads environment variables and contains no HTTP client.
    """

    def __init__(
        self,
        *,
        database_path: str | Path | None = None,
        embedding_function: EmbeddingFunction | None = None,
        max_entries: int = 1_000,
    ) -> None:
        if max_entries < 1:
            raise MemoryContractError("max_entries must be positive.")
        self._database_path = Path(database_path).resolve() if database_path else None
        self._embedding_function = embedding_function
        self._max_entries = max_entries
        self._entries: dict[str, MemoryEntry] = {}
        if self._database_path is not None:
            self._initialize_database()
            self._load_entries()

    def _connect(self) -> sqlite3.Connection:
        if self._database_path is None:
            raise MemoryContractError("Persistence is not configured.")
        return sqlite3.connect(self._database_path)

    def _initialize_database(self) -> None:
        if self._database_path is None:
            raise MemoryContractError("Persistence is not configured.")
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS memory_entries ("
                "entry_id TEXT PRIMARY KEY, text TEXT NOT NULL, metadata TEXT NOT NULL, "
                "embedding TEXT)"
            )

    def _load_entries(self) -> None:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT entry_id, text, metadata, embedding FROM memory_entries ORDER BY rowid"
            ).fetchall()
        for entry_id, text, metadata_json, embedding_json in rows:
            metadata = json.loads(metadata_json)
            embedding = tuple(json.loads(embedding_json)) if embedding_json else None
            self._entries[entry_id] = self._entry(entry_id, text, metadata, embedding)

    @staticmethod
    def validate_metadata(
        metadata: Mapping[str, MetadataValue] | None,
    ) -> dict[str, MetadataValue]:
        values = dict(metadata or {})
        if len(values) > 20:
            raise MemoryContractError("Memory metadata is limited to 20 fields.")
        for key, value in values.items():
            if not key or len(key) > 64 or not re.fullmatch(r"[a-zA-Z0-9_.-]+", key):
                raise MemoryContractError("Memory metadata keys must be bounded identifiers.")
            if isinstance(value, str) and len(value) > 500:
                raise MemoryContractError("Memory metadata strings are limited to 500 characters.")
        return values

    @staticmethod
    def _entry(
        entry_id: str,
        text: str,
        metadata: Mapping[str, MetadataValue],
        embedding: Sequence[float] | None,
    ) -> MemoryEntry:
        return MemoryEntry(
            entry_id=entry_id,
            text=text,
            metadata=MappingProxyType(dict(metadata)),
            embedding=tuple(float(value) for value in embedding) if embedding else None,
        )

    def store(
        self,
        text: str,
        metadata: Mapping[str, MetadataValue] | None = None,
        *,
        confirmed: bool = False,
    ) -> MemoryEntry:
        if not confirmed:
            raise MemoryApprovalRequiredError("Memory writes require explicit confirmation.")
        normalized = text.strip()
        if not normalized or len(normalized) > 10_000:
            raise MemoryContractError("Memory text must contain 1 to 10000 visible characters.")
        if len(self._entries) >= self._max_entries:
            raise MemoryContractError("Memory entry limit reached.")
        values = self.validate_metadata(metadata)
        embedding = self._embedding_function(normalized) if self._embedding_function else None
        entry = self._entry(uuid4().hex, normalized, values, embedding)
        self._entries[entry.entry_id] = entry
        if self._database_path is not None:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO memory_entries(entry_id, text, metadata, embedding) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        entry.entry_id,
                        entry.text,
                        json.dumps(dict(entry.metadata), sort_keys=True),
                        json.dumps(entry.embedding) if entry.embedding else None,
                    ),
                )
        return entry

    def list_entries(self) -> tuple[MemoryEntry, ...]:
        return tuple(self._entries.values())

    def search(self, query: str, *, limit: int = 5) -> tuple[tuple[MemoryEntry, float], ...]:
        normalized = query.strip()
        if not normalized or len(normalized) > 5_000 or not 1 <= limit <= 50:
            raise MemoryContractError("Memory search request is outside bounded limits.")
        query_embedding = self._embedding_function(normalized) if self._embedding_function else None
        query_tokens = _tokens(normalized)
        scored: list[tuple[MemoryEntry, float]] = []
        for entry in self._entries.values():
            if query_embedding is not None and entry.embedding is not None:
                score = _cosine(query_embedding, entry.embedding)
            else:
                entry_tokens = _tokens(entry.text)
                combined_tokens = query_tokens | entry_tokens
                score = (
                    len(query_tokens & entry_tokens) / len(combined_tokens)
                    if combined_tokens
                    else 0.0
                )
            if score > 0:
                scored.append((entry, score))
        scored.sort(key=lambda item: (-item[1], item[0].entry_id))
        return tuple(scored[:limit])

    def delete(self, entry_id: str, *, confirmed: bool = False) -> bool:
        if not confirmed:
            raise MemoryApprovalRequiredError("Memory deletion requires explicit confirmation.")
        removed = self._entries.pop(entry_id, None)
        if removed is None:
            return False
        if self._database_path is not None:
            with self._connect() as connection:
                connection.execute("DELETE FROM memory_entries WHERE entry_id = ?", (entry_id,))
        return True
