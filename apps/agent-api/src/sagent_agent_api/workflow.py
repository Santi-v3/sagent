"""Deterministic planning and approval workflow without side effects."""

from datetime import UTC, datetime
from threading import RLock
from uuid import UUID, uuid4

from sagent_agent_api.models import (
    ApprovalState,
    ChangeProposal,
    PlannedTask,
    PlanStep,
    RiskLevel,
)


class TaskNotFoundError(KeyError):
    """Raised when a workflow task does not exist."""


class InvalidTransitionError(ValueError):
    """Raised when an approval decision targets a terminal task."""


class TaskPlanner:
    """Create reproducible plans from user text without an LLM."""

    @staticmethod
    def create_plan(task: str) -> PlannedTask:
        normalized_task = task.strip()
        now = datetime.now(UTC)
        return PlannedTask(
            task_id=uuid4(),
            task=normalized_task,
            goal=f"Die Aufgabe „{normalized_task}“ sicher und nachvollziehbar vorbereiten.",
            steps=[
                PlanStep(
                    position=1,
                    title="Kontext prüfen",
                    description="Relevante Anforderungen, Grenzen und Abhängigkeiten erfassen.",
                ),
                PlanStep(
                    position=2,
                    title="Umsetzung strukturieren",
                    description="Änderungen in kleine, überprüfbare Schritte zerlegen.",
                ),
                PlanStep(
                    position=3,
                    title="Änderungsvorschlag prüfen",
                    description="Betroffene Bereiche, Risiken und Freigaben sichtbar machen.",
                ),
                PlanStep(
                    position=4,
                    title="Menschliche Entscheidung abwarten",
                    description="Ohne Freigabe keine Datei- oder Systemaktion ausführen.",
                ),
            ],
            risks=[
                "Der Plan basiert ausschließlich auf dem eingegebenen Aufgabentext.",
                (
                    "Betroffene Dateien können erst nach einer sicheren Projektanalyse "
                    "bestätigt werden."
                ),
                (
                    "Diese Phase verändert keine Dateien. Testbefehle laufen nur nach "
                    "Freigabe und separater Auswahl."
                ),
            ],
            next_actions=[
                "Plan und Risiken prüfen",
                "Änderungsvorschlag bewerten",
                "Freigeben, ablehnen oder Überarbeitung anfordern",
            ],
            proposal=ChangeProposal(
                summary=f"Kontrollierte Umsetzung für „{normalized_task}“ vorbereiten.",
                risk_level=RiskLevel.LOW,
                affected_files=TaskPlanner._infer_affected_files(normalized_task),
                required_approvals=["human_review"],
            ),
            approval_state=ApprovalState.PENDING,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _infer_affected_files(task: str) -> list[str]:
        normalized = task.casefold()
        candidates = [
            (("api", "backend", "fastapi"), "apps/agent-api/"),
            (("web", "frontend", "next.js", "ui", "oberfläche"), "apps/web/"),
            (("memory", "gedächtnis"), "packages/memory/"),
            (("tool", "werkzeug"), "packages/tools/"),
            (("dokument", "docs", "handoff", "readme"), "docs/"),
        ]
        return [
            path for keywords, path in candidates if any(word in normalized for word in keywords)
        ]


class WorkflowStore:
    """Thread-safe in-memory storage for the simulated workflow."""

    def __init__(self) -> None:
        self._tasks: dict[UUID, PlannedTask] = {}
        self._lock = RLock()

    def create(self, task: str) -> PlannedTask:
        planned_task = TaskPlanner.create_plan(task)
        with self._lock:
            self._tasks[planned_task.task_id] = planned_task
        return planned_task.model_copy(deep=True)

    def get(self, task_id: UUID) -> PlannedTask:
        with self._lock:
            planned_task = self._tasks.get(task_id)
            if planned_task is None:
                raise TaskNotFoundError(task_id)
            return planned_task.model_copy(deep=True)

    def decide(self, task_id: UUID, decision: ApprovalState) -> PlannedTask:
        with self._lock:
            planned_task = self._tasks.get(task_id)
            if planned_task is None:
                raise TaskNotFoundError(task_id)
            if planned_task.approval_state is not ApprovalState.PENDING:
                raise InvalidTransitionError(
                    f"Task is already {planned_task.approval_state.value}."
                )

            updated = planned_task.model_copy(
                update={
                    "approval_state": decision,
                    "updated_at": datetime.now(UTC),
                },
                deep=True,
            )
            self._tasks[task_id] = updated
            return updated.model_copy(deep=True)


workflow_store = WorkflowStore()
