"""FastAPI application for Sagent's first local technical slice."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from sagent_agent_api.models import (
    ApprovalRequest,
    ApprovalResponse,
    ApprovalState,
    HealthResponse,
    PlannedTask,
    TaskRequest,
    TaskResponse,
    TestProfileResponse,
    TestResultResponse,
    TestRunRequest,
)
from sagent_agent_api.test_execution import get_test_runner
from sagent_agent_api.workflow import (
    InvalidTransitionError,
    TaskNotFoundError,
    workflow_store,
)
from sagent_tools import (
    TestCommandMismatchError,
    TestExecutionError,
    TestProfileNotAllowedError,
    TestResultNotFoundError,
    TestRunner,
    TestRunnerBusyError,
)

TestRunnerDependency = Annotated[TestRunner, Depends(get_test_runner)]

app = FastAPI(
    title="Sagent Agent API",
    description="Local deterministic API placeholder for Sagent.",
    version="0.3.0",
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


@app.get("/agent/test-profiles", response_model=list[TestProfileResponse])
def list_test_profiles(
    runner: TestRunnerDependency,
) -> list[TestProfileResponse]:
    """List safe display metadata for the fixed server-side test allowlist."""

    return [TestProfileResponse.model_validate(profile) for profile in runner.list_profiles()]


@app.post("/agent/run-tests", response_model=TestResultResponse)
def run_tests(
    request: TestRunRequest,
    runner: TestRunnerDependency,
) -> TestResultResponse:
    """Run one reviewed allowlist profile for an explicitly approved task."""

    try:
        task = workflow_store.get(request.task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail="Task not found.") from error
    if task.approval_state is not ApprovalState.APPROVED:
        raise HTTPException(
            status_code=409,
            detail="Task must be approved before tests can run.",
        )

    try:
        result = runner.run(request.profile_id, request.expected_command)
    except TestProfileNotAllowedError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TestCommandMismatchError, TestRunnerBusyError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except TestExecutionError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    return TestResultResponse.model_validate(result)


@app.get("/agent/test-results/{result_id}", response_model=TestResultResponse)
def get_test_result(
    result_id: UUID,
    runner: TestRunnerDependency,
) -> TestResultResponse:
    """Return one stored, bounded test result."""

    try:
        result = runner.get(result_id)
    except TestResultNotFoundError as error:
        raise HTTPException(status_code=404, detail="Test result not found.") from error
    return TestResultResponse.model_validate(result)
