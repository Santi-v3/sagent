"""FastAPI application for Sagent's first local technical slice."""

from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from sagent_agent_api.models import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalState,
    HealthResponse,
    PlannedTask,
    TaskRequest,
    TaskResponse,
)
from sagent_agent_api.workflow import (
    InvalidTransitionError,
    TaskNotFoundError,
    workflow_store,
)

app = FastAPI(
    title="Sagent Agent API",
    description="Local deterministic API placeholder for Sagent.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return a small, deterministic service health response."""

    return HealthResponse(status="ok", service="sagent-agent-api")


@app.post("/agent/task", response_model=TaskResponse)
def create_task(request: TaskRequest) -> TaskResponse:
    """Acknowledge a task without running tools, models, or mutations."""

    task = request.task.strip()
    if not task:
        # Pydantic catches empty input; this also rejects whitespace-only tasks.
        raise HTTPException(status_code=422, detail="Task must contain visible text.")

    return TaskResponse(
        status="accepted",
        message=(
            f"Aufgabe „{task}“ wurde lokal angenommen. "
            "Diese Minimalversion führt noch keine Änderungen aus."
        ),
        next_steps=[
            "Anforderungen und Projektkontext prüfen",
            "Einen kontrollierten Arbeitsplan vorbereiten",
            "Vor jeder Änderung eine Freigabe einholen",
        ],
    )


@app.post("/agent/plan", response_model=PlannedTask, status_code=status.HTTP_201_CREATED)
def create_plan(request: TaskRequest) -> PlannedTask:
    """Create and store a deterministic, non-executing implementation plan."""

    task = request.task.strip()
    if not task:
        raise HTTPException(status_code=422, detail="Task must contain visible text.")
    return workflow_store.create(task)


@app.get("/agent/tasks/{task_id}", response_model=PlannedTask)
def get_planned_task(task_id: UUID) -> PlannedTask:
    """Return the current planning and approval state for a task."""

    try:
        return workflow_store.get(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail="Task not found.") from error


@app.post("/agent/approve", response_model=ApprovalResponse)
def approve_task(request: ApprovalRequest) -> ApprovalResponse:
    """Apply a human decision to a pending simulated proposal."""

    try:
        updated = workflow_store.decide(
            request.task_id,
            ApprovalState(request.decision),
        )
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail="Task not found.") from error
    except InvalidTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    messages = {
        ApprovalState.APPROVED: "Änderungsvorschlag wurde freigegeben.",
        ApprovalState.REJECTED: "Änderungsvorschlag wurde abgelehnt.",
        ApprovalState.NEEDS_CHANGES: "Überarbeitung wurde angefordert.",
    }
    return ApprovalResponse(message=messages[updated.approval_state], task=updated)
