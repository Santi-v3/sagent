import json
import math
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class MemoryEntry:
    id: str
    text: str
    embedding: list[float] | None
    metadata: dict[str, Any]
    created_at: float
    parent_id: str | None = None  # For chunked entries: links to original parent


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(ai * bi for ai, bi in zip(a, b, strict=False))
    na = math.sqrt(sum(ai * ai for ai in a))
    nb = math.sqrt(sum(bi * bi for bi in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


_DB_PATH: str | None = None


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = os.environ.get("SAGENT_MEMORY_DB", os.path.join(os.path.expanduser("~"), ".sagent", "memory.db"))
    return _DB_PATH


def set_db_path(path: str) -> None:
    global _DB_PATH
    _DB_PATH = path


# Chunking configuration
_CHUNK_MAX_CHARS = 800
_CHUNK_OVERLAP = 100


def _chunk_text(text: str, max_chars: int = _CHUNK_MAX_CHARS, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks at paragraph/sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Try to break at paragraph boundary
        para = text.rfind("\n\n", start, end)
        if para > start + max_chars // 2:
            chunks.append(text[start:para])
            start = para
            continue
        # Try to break at sentence boundary
        sentence = max(
            text.rfind(". ", start, end),
            text.rfind("! ", start, end),
            text.rfind("? ", start, end),
            text.rfind("\n", start, end),
        )
        if sentence > start + max_chars // 3:
            chunks.append(text[start:sentence + 1])
            start = sentence + 1
        else:
            chunks.append(text[start:end])
            start = end
        # Apply overlap
        if overlap > 0 and start < len(text):
            start = max(0, start - overlap)
    return chunks


class MemoryPersistence:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or _get_db_path()
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at REAL NOT NULL,
                    parent_id TEXT
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_memories_parent ON memories(parent_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(metadata)")

    def load_all(self) -> list[MemoryEntry]:
        with self._conn() as c:
            rows = c.execute("SELECT id, text, embedding, metadata, created_at, parent_id FROM memories ORDER BY created_at").fetchall()
        result: list[MemoryEntry] = []
        for r in rows:
            emb = json.loads(r["embedding"]) if r["embedding"] else None
            meta = json.loads(r["metadata"])
            result.append(MemoryEntry(id=r["id"], text=r["text"], embedding=emb, metadata=meta, created_at=r["created_at"], parent_id=r["parent_id"]))
        return result

    def save(self, entry: MemoryEntry) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO memories (id, text, embedding, metadata, created_at, parent_id) VALUES (?, ?, ?, ?, ?, ?)",
                (entry.id, entry.text, json.dumps(entry.embedding) if entry.embedding else None, json.dumps(entry.metadata), entry.created_at, entry.parent_id),
            )

    def delete(self, entry_id: str) -> bool:
        with self._conn() as c:
            c.execute("DELETE FROM memories WHERE id = ? OR parent_id = ?", (entry_id, entry_id))
            return c.rowcount > 0

    def clear(self) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM memories")


class MemoryService:
    def __init__(self, ollama_base_url: str = "http://127.0.0.1:11434", embedding_model: str = "nomic-embed-text", db_path: str | None = None) -> None:
        self._ollama_base_url = ollama_base_url.rstrip("/")
        self._embedding_model = embedding_model
        self._db = MemoryPersistence(db_path)
        self._entries: list[MemoryEntry] = self._db.load_all()

    def _embed(self, text: str) -> list[float] | None:
        import httpx2 as httpx_module
        try:
            r = httpx_module.post(
                f"{self._ollama_base_url}/api/embeddings",
                json={"model": self._embedding_model, "prompt": text},
                timeout=30.0,
            )
            r.raise_for_status()
            return r.json()["embedding"]
        except Exception:
            return None

    def store(self, text: str, metadata: dict[str, Any] | None = None, chunk: bool = True) -> MemoryEntry:
        """Store text with optional chunking for long texts.
        
        Returns the first/parent entry. Chunks are stored as additional entries
        with parent_id pointing to the first entry.
        """
        meta = metadata or {}
        parent_id = uuid.uuid4().hex[:12]

        if chunk and len(text) > _CHUNK_MAX_CHARS:
            chunks = _chunk_text(text)
            first_entry = None
            for i, chunk_text in enumerate(chunks):
                chunk_meta = {**meta, "chunk": i, "total_chunks": len(chunks)}
                entry = MemoryEntry(
                    id=uuid.uuid4().hex[:12],
                    text=chunk_text,
                    embedding=None,
                    metadata=chunk_meta,
                    created_at=time.time(),
                    parent_id=parent_id if i > 0 else None,
                )
                emb = self._embed(chunk_text)
                if emb is not None:
                    entry.embedding = emb
                self._entries.append(entry)
                self._db.save(entry)
                if i == 0:
                    first_entry = entry
            return first_entry  # type: ignore[return-value]

        entry = MemoryEntry(
            id=parent_id,
            text=text,
            embedding=None,
            metadata=meta,
            created_at=time.time(),
        )
        emb = self._embed(text)
        if emb is not None:
            entry.embedding = emb
        self._entries.append(entry)
        self._db.save(entry)
        return entry

    def search(self, query: str, n_results: int = 5, category: str | None = None) -> list[tuple[MemoryEntry, float]]:
        """Semantic search with optional category filter.
        
        Returns list of (entry, score) tuples sorted by relevance.
        """
        q_emb = self._embed(query)
        if q_emb is None:
            return []
        scored: list[tuple[MemoryEntry, float]] = []
        for e in self._entries:
            if e.embedding is not None:
                if category and e.metadata.get("category") != category:
                    continue
                score = _cosine_similarity(q_emb, e.embedding)
                scored.append((e, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:n_results]

    def search_grouped(self, query: str, n_groups: int = 3, category: str | None = None) -> list[tuple[MemoryEntry, float]]:
        """Search and group chunked results, returning the best chunk per parent."""
        results = self.search(query, n_results=50, category=category)
        # Group by parent_id
        groups: dict[str, list[tuple[MemoryEntry, float]]] = {}
        for entry, score in results:
            gid = entry.parent_id or entry.id
            if gid not in groups:
                groups[gid] = []
            groups[gid].append((entry, score))
        # Pick best from each group
        best_per_group: list[tuple[MemoryEntry, float]] = []
        for gid, entries in groups.items():
            best = max(entries, key=lambda x: x[1])
            best_per_group.append(best)
        best_per_group.sort(key=lambda x: x[1], reverse=True)
        return best_per_group[:n_groups]

    def list_all(self) -> list[MemoryEntry]:
        return list(self._entries)

    def get(self, entry_id: str) -> MemoryEntry | None:
        for e in self._entries:
            if e.id == entry_id:
                return e
        return None

    def delete(self, entry_id: str) -> bool:
        for i in range(len(self._entries) - 1, -1, -1):
            if self._entries[i].id == entry_id or self._entries[i].parent_id == entry_id:
                self._entries.pop(i)
        self._db.delete(entry_id)
        return True

    def clear(self) -> None:
        self._entries.clear()
        self._db.clear()
