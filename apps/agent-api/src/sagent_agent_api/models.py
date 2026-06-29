"""Request and response models for the local Agent API."""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class ApprovalState(StrEnum):
    """Human decision state for a simulated change proposal."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


class RiskLevel(StrEnum):
    """Coarse risk classification for a proposed change."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PlanStep(BaseModel):
    """One deterministic step in a proposed implementation plan."""

    position: int = Field(ge=1)
    title: str
    description: str


class ChangeProposal(BaseModel):
    """A non-executing description of potential project changes."""

    summary: str
    risk_level: RiskLevel
    affected_files: list[str]
    required_approvals: list[str]


class PlannedTask(BaseModel):
    """Stored planning state for one simulated developer-agent task."""

    task_id: UUID
    task: str
    goal: str
    steps: list[PlanStep]
    risks: list[str]
    next_actions: list[str]
    proposal: ChangeProposal
    approval_state: ApprovalState
    created_at: datetime
    updated_at: datetime


class ApprovalRequest(BaseModel):
    """A human decision for an existing planned task."""

    task_id: UUID
    decision: Literal["approved", "rejected", "needs_changes"]
    comment: str | None = Field(default=None, max_length=1_000)


class ApprovalResponse(BaseModel):
    """Updated task state after a valid human decision."""

    message: str
    task: PlannedTask


class TestProfileResponse(BaseModel):
    """An allowlisted command that can be reviewed before execution."""

    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    command: str
    working_directory: str
    timeout_seconds: float


class TestRunRequest(BaseModel):
    """Explicit confirmation of one displayed test profile for an approved task."""

    task_id: UUID
    profile_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")
    expected_command: str = Field(min_length=1, max_length=500)
    confirmed: Literal[True]


class TestResultResponse(BaseModel):
    """Bounded and redacted output from one allowlisted test run."""

    model_config = ConfigDict(from_attributes=True)

    result_id: UUID
    profile_id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    passed: bool
    created_at: datetime
    duration_ms: int = Field(ge=0)
    timed_out: bool
    output_truncated: bool


class GitFileStatusResponse(BaseModel):
    """One visible Git status entry with sensitive paths hidden."""

    model_config = ConfigDict(from_attributes=True)

    path: str
    index_status: str
    worktree_status: str
    original_path: str | None
    sensitive: bool


class GitStatusResponse(BaseModel):
    """Structured branch and worktree state for the fixed repository."""

    model_config = ConfigDict(from_attributes=True)

    branch: str | None
    detached: bool
    is_main: bool
    clean: bool
    ahead: int = Field(ge=0)
    behind: int = Field(ge=0)
    head_sha: str | None
    files: list[GitFileStatusResponse]
    warning: str | None


class GitDiffResponse(BaseModel):
    """Bounded and redacted review diff."""

    model_config = ConfigDict(from_attributes=True)

    patch: str
    diff_hash: str
    file_count: int = Field(ge=0)
    truncated: bool
    secrets_redacted: bool
    sensitive_paths_hidden: int = Field(ge=0)


class GitBranchRequest(BaseModel):
    """Explicit request for one policy-compliant local feature branch."""

    name: str = Field(min_length=3, max_length=100)
    expected_current_branch: str | None = Field(default=None, max_length=100)
    confirmed: Literal[True]


class GitBranchResponse(BaseModel):
    """Updated repository state after creating a local feature branch."""

    message: str
    status: GitStatusResponse
