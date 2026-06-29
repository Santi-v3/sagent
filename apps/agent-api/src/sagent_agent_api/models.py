"""Request and response models for the minimal Agent API."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Describe the local API health state."""

    status: Literal["ok"]
    service: Literal["sagent-agent-api"]


class TaskRequest(BaseModel):
    """A single user task accepted by the placeholder API."""

    task: str = Field(min_length=1, max_length=4_000)


class TaskResponse(BaseModel):
    """A deterministic acknowledgement without agent execution."""

    status: Literal["accepted"]
    message: str
    next_steps: list[str]
