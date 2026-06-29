"""FastAPI application for Sagent's first local technical slice."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from sagent_agent_api.models import HealthResponse, TaskRequest, TaskResponse

app = FastAPI(
    title="Sagent Agent API",
    description="Local deterministic API placeholder for Sagent.",
    version="0.1.0",
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
