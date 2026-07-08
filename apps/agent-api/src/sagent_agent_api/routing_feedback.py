"""Learns from user routing decisions to improve future task routing."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

FEEDBACK_FILE = Path.home() / ".sagent" / "routing_feedback.json"


@dataclass
class RoutingFeedbackEntry:
    task_type: str
    complexity: str
    keywords: list[str]
    adapter_id: str
    transport: str
    success: bool
    timestamp: float


class RoutingFeedbackStore:
    """Stores and learns from past routing decisions."""

    def __init__(self, path: Path = FEEDBACK_FILE) -> None:
        self._lock = Lock()
        self._path = path
        self._entries: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            if self._path.exists():
                with open(self._path) as f:
                    self._entries = json.load(f)
        except Exception:
            self._entries = []

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w") as f:
                json.dump(self._entries[-500:], f, indent=2)
        except Exception:
            pass

    def record(
        self,
        task: str,
        task_type: str,
        complexity: str,
        adapter_id: str,
        transport: str,
        success: bool = True,
    ) -> None:
        """Record a routing decision for future reference."""
        import re

        keywords = [w.lower() for w in re.findall(r"[a-zA-ZäöüßÄÖÜ]{3,}", task) if w.lower() not in STOPWORDS][:10]
        entry = {
            "task_type": task_type,
            "complexity": complexity,
            "keywords": keywords,
            "adapter_id": adapter_id,
            "transport": transport,
            "success": success,
            "timestamp": time.time(),
        }
        with self._lock:
            self._entries.append(entry)
            self._save()

    def suggest_adapter(self, task: str, task_type: str, complexity: str, available: list[str]) -> str | None:
        """Return the most frequently used adapter for similar tasks."""
        import re

        keywords = {w.lower() for w in re.findall(r"[a-zA-ZäöüßÄÖÜ]{3,}", task) if w.lower() not in STOPWORDS}
        candidates: dict[str, float] = {}
        with self._lock:
            for entry in self._entries[-200:]:  # recent entries only
                if entry.get("task_type") != task_type:
                    continue
                if not entry.get("success"):
                    continue
                entry_kw = set(entry.get("keywords", []))
                overlap = len(keywords & entry_kw)
                if overlap < 2:
                    continue
                score = overlap + (1 if entry.get("complexity") == complexity else 0)
                aid = entry.get("adapter_id", "")
                if aid in available:
                    candidates[aid] = candidates.get(aid, 0) + score

        if not candidates:
            return None
        best = max(candidates, key=candidates.get)
        if candidates[best] < 3:  # minimum threshold
            return None
        return best


STOPWORDS = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem",
    "eines", "mit", "von", "für", "auf", "über", "unter", "und", "oder", "aber",
    "nicht", "kein", "keine", "ist", "wird", "wurde", "hat", "haben", "sind",
    "bitte", "kann", "können", "soll", "sollen", "werden", "dass", "the", "a",
    "an", "of", "in", "to", "for", "with", "on", "at", "by", "this", "that",
    "it", "is", "was", "are", "be", "been", "has", "have", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can", "need",
    "darf", "dürfen", "muss", "müssen", "please", "make", "help",
}


_singleton: RoutingFeedbackStore | None = None


def get_feedback_store() -> RoutingFeedbackStore:
    global _singleton
    if _singleton is None:
        _singleton = RoutingFeedbackStore()
    return _singleton


def close_feedback_store() -> None:
    global _singleton
    _singleton = None
