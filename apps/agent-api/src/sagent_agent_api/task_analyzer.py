import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Complexity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskType(Enum):
    QUERY = "query"
    CODE = "code"
    ARCHITECTURE = "architecture"
    DEBUG = "debug"
    RESEARCH = "research"
    REFACTOR = "refactor"
    CONFIG = "config"
    EXPLAIN = "explain"
    REVIEW = "review"
    SEARCH = "search"


@dataclass
class TaskProfile:
    complexity: Complexity = Complexity.LOW
    task_type: TaskType = TaskType.QUERY
    required_tools: list[str] = field(default_factory=list)
    estimated_steps: int = 1
    estimated_tokens: int = 500
    needs_vision: bool = False
    needs_reasoning: bool = False
    needs_long_context: bool = False
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "complexity": self.complexity.value,
            "task_type": self.task_type.value,
            "required_tools": self.required_tools,
            "estimated_steps": self.estimated_steps,
            "estimated_tokens": self.estimated_tokens,
            "needs_vision": self.needs_vision,
            "needs_reasoning": self.needs_reasoning,
            "needs_long_context": self.needs_long_context,
            "confidence": self.confidence,
        }


@dataclass
class RoutingDecision:
    target: str
    reason: str
    profile: TaskProfile | None = None
    suggested_adapter: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "reason": self.reason,
            "suggested_adapter": self.suggested_adapter,
            "profile": self.profile.to_dict() if self.profile else None,
        }


def _count_tokens(text: str) -> int:
    return len(text) // 4


def _estimate_steps(task: str, task_type: TaskType) -> int:
    if task_type in (TaskType.QUERY, TaskType.EXPLAIN, TaskType.SEARCH):
        return 1
    if task_type == TaskType.CONFIG:
        return 2
    if task_type in (TaskType.DEBUG, TaskType.REVIEW):
        return 3
    if task_type == TaskType.REFACTOR:
        return 5
    if task_type == TaskType.ARCHITECTURE:
        return 8
    return 3


_COMPLEXITY_KEYWORDS: dict[str, int] = {
    "architektur": 3, "design pattern": 3, "refactor": 3, "umstellen": 3,
    "migrate": 3, "migration": 3, "neu schreiben": 3, "rewrite": 3,
    "komplex": 3, "optimieren": 2, "performance": 2, "testen": 2,
    "debuggen": 2, "fehler": 2, "bug": 2, "problem": 2,
}

_TOOL_KEYWORDS: dict[str, list[str]] = {
    "bash": ["bash", "shell", "terminal", "command", "ausführen", "installieren", "starten", "stop"],
    "write_file": ["schreiben", "erstellen", "datei", "file", "neu"],
    "edit_file": ["ändern", "edit", "bearbeiten", "update", "aktualisieren", "hinzufügen"],
    "read_file": ["lesen", "anzeigen", "cat"],
    "grep": ["suchen", "finden", "search", "grep"],
    "glob": ["dateien finden", "list", "alle"],
    "git_status": ["git status", "änderungen", "branch"],
    "git_commit": ["commit", "committen"],
    "run_tests": ["test", "testen", "prüfen"],
}

_TASK_TYPE_KEYWORDS: dict[TaskType, list[str]] = {
    TaskType.QUERY: ["was ist", "wie", "frage", "erkläre", "bedeutet"],
    TaskType.CODE: ["schreib", "code", "implementiere", "funktion", "klasse", "api", "endpoint"],
    TaskType.ARCHITECTURE: ["architektur", "design", "struktur", "aufbau", "konzept"],
    TaskType.DEBUG: ["bug", "fehler", "error", "debug", "kaputt", "funktioniert nicht"],
    TaskType.RESEARCH: ["recherchiere", "finde heraus", "google", "suche info"],
    TaskType.REFACTOR: ["refactor", "umstrukturieren", "verbessern", "optimieren", "vereinfachen"],
    TaskType.CONFIG: ["konfigurieren", "config", "einstellen", "setup", "install"],
    TaskType.EXPLAIN: ["erkläre", "beschreibe", "was macht", "wie funktioniert"],
    TaskType.REVIEW: ["review", "prüfen", "check", "analysiere", "code review"],
    TaskType.SEARCH: ["suche", "finde", "search", "lookup"],
}

_VISION_KEYWORDS = ["bild", "image", " screenshot", "ocr", "foto", "diagramm", "grafik",
                    "screen", "abbildung", "figur"]


def _classify_task_type(task: str) -> TaskType:
    task_lower = task.lower()
    scores: dict[TaskType, int] = {}
    for tt, keywords in _TASK_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in task_lower)
        if score > 0:
            scores[tt] = score
    if not scores:
        return TaskType.QUERY
    return max(scores, key=scores.get)


def _estimate_complexity(task: str, task_type: TaskType) -> Complexity:
    task_lower = task.lower()
    score = 0
    for kw, weight in _COMPLEXITY_KEYWORDS.items():
        if kw in task_lower:
            score += weight

    if task_type in (TaskType.ARCHITECTURE, TaskType.REFACTOR):
        score += 2
    if task_type == TaskType.DEBUG:
        score += 1
    if len(task) > 500:
        score += 2
    elif len(task) > 200:
        score += 1

    if score >= 4:
        return Complexity.HIGH
    if score >= 2:
        return Complexity.MEDIUM
    return Complexity.LOW


def _estimate_required_tools(task: str) -> list[str]:
    task_lower = task.lower()
    tools: list[str] = []
    for tool, keywords in _TOOL_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            tools.append(tool)
    return tools[:4]


def analyze_task(task: str) -> TaskProfile:
    task_type = _classify_task_type(task)
    complexity = _estimate_complexity(task, task_type)
    required_tools = _estimate_required_tools(task)
    estimated_steps = _estimate_steps(task, task_type)
    estimated_tokens = _count_tokens(task) + estimated_steps * 500

    task_lower = task.lower()
    needs_vision = any(kw in task_lower for kw in _VISION_KEYWORDS)
    needs_reasoning = complexity in (Complexity.HIGH, Complexity.MEDIUM)
    needs_long_context = estimated_tokens > 8000

    confidence = min(0.5 + len(required_tools) * 0.1 + (complexity.value == "high") * 0.2, 0.95)

    return TaskProfile(
        complexity=complexity,
        task_type=task_type,
        required_tools=required_tools,
        estimated_steps=estimated_steps,
        estimated_tokens=estimated_tokens,
        needs_vision=needs_vision,
        needs_reasoning=needs_reasoning,
        needs_long_context=needs_long_context,
        confidence=confidence,
    )


def route_task(
    profile: TaskProfile,
    available_adapters: list[dict[str, Any]],
    user_models: list[dict[str, Any]] | None = None,
    local_usage_remaining: int | None = None,
) -> RoutingDecision:
    has_local = any(
        a.get("transport") != "remote_http" and not a.get("simulated")
        for a in available_adapters
    )
    has_cloud = any(
        a.get("transport") == "remote_http" and not a.get("simulated")
        for a in available_adapters
    ) or (user_models and len(user_models) > 0)

    if profile.estimated_steps <= 1 and profile.complexity == Complexity.LOW and has_local:
        return RoutingDecision(
            target="local",
            reason="Einfache Anfrage – lokales Modell ist schnell und verbraucht kein Cloud-Kontingent.",
            profile=profile,
        )

    if profile.estimated_steps >= 5 and profile.complexity == Complexity.HIGH and has_cloud:
        best_cloud = None
        for a in available_adapters:
            if a.get("transport") == "remote_http":
                best_cloud = a.get("adapter_id")
                break
        if not best_cloud and user_models:
            best_cloud = user_models[0].get("id")
        return RoutingDecision(
            target="cloud",
            reason=f"Komplexe Aufgabe ({profile.complexity.value}, ~{profile.estimated_steps} Schritte) – Cloud-Modell empfohlen.",
            profile=profile,
            suggested_adapter=best_cloud,
        )

    if profile.needs_reasoning and has_cloud:
        return RoutingDecision(
            target="cloud",
            reason="Aufgabe benötigt Reasoning – Cloud-Modell ist leistungsstärker.",
            profile=profile,
        )

    if local_usage_remaining is not None and local_usage_remaining <= 0 and has_cloud:
        return RoutingDecision(
            target="cloud",
            reason="Lokales Usage-Limit erreicht – weiche auf Cloud aus.",
            profile=profile,
        )

    if has_local:
        return RoutingDecision(
            target="local",
            reason="Ausgewogen: lokales Modell kann diese Aufgabe bewältigen.",
            profile=profile,
        )

    if has_cloud:
        return RoutingDecision(
            target="cloud",
            reason="Kein lokales Modell verfügbar – nutze Cloud.",
            profile=profile,
        )

    return RoutingDecision(
        target="local",
        reason="Standard: lokales Modell (keine Cloud verfügbar).",
        profile=profile,
    )
