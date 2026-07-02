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


class ModelAdapterResponse(BaseModel):
    """Reviewable model adapter metadata without credentials or endpoint details."""

    adapter_id: str
    provider: str
    model: str
    capabilities: list[Literal["chat", "coding"]]
    transport: Literal["in_process", "loopback_http", "remote_http"]
    simulated: bool
    supports_streaming: bool


class ModelPreviewRequest(BaseModel):
    """Bounded prompt for the deterministic offline adapter."""

    prompt: str = Field(min_length=1, max_length=8_000)
    capability: Literal["chat", "coding"] = "chat"
    max_output_tokens: int = Field(default=256, ge=1, le=2_048)


class ModelPreviewResponse(BaseModel):
    """Untrusted text returned by the currently selected adapter."""

    request_id: UUID
    adapter_id: str
    model: str
    content: str
    finish_reason: Literal["stop", "length"]
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    untrusted: Literal[True]
    simulated: Literal[True]


class LocalModelCompletionRequest(BaseModel):
    """Explicitly confirmed call to one preconfigured loopback adapter."""

    adapter_id: str = Field(pattern=r"^[a-z][a-z0-9._-]{0,63}$")
    prompt: str = Field(min_length=1, max_length=8_000)
    capability: Literal["chat", "coding"] = "chat"
    max_output_tokens: int = Field(default=256, ge=1, le=2_048)
    confirmed: Literal[True]


class LocalModelCompletionResponse(BaseModel):
    """Untrusted text returned from an explicitly configured loopback adapter."""

    request_id: UUID
    adapter_id: str
    model: str
    content: str
    finish_reason: Literal["stop", "length"]
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    untrusted: Literal[True]
    simulated: Literal[False]


class ModelJobCreateRequest(BaseModel):
    """Explicit request for one cancellable local model job."""

    adapter_id: str = Field(pattern=r"^[a-z][a-z0-9._-]{0,63}$")
    prompt: str = Field(min_length=1, max_length=8_000)
    capability: Literal["chat", "coding"] = "chat"
    max_output_tokens: int = Field(default=256, ge=1, le=2_048)
    confirmed: Literal[True]


class CloudApprovalPreviewDisclosureRequest(BaseModel):
    """Safe disclosure metadata for a cloud approval preview request."""

    repo_context_included: bool = False
    diffs_included: bool = False
    files_included: bool = False
    data_was_redacted: bool = False
    bytes_estimate: int = 0


class CloudApprovalPreviewRequest(BaseModel):
    """Read-only metadata request for an offline cloud approval preview.

    No files, endpoints, API keys, or network configuration is accepted.
    """

    provider_id: str = "deepseek-cloud"
    purpose: Literal["coding", "architecture", "debugging"] = "coding"
    disclosure: CloudApprovalPreviewDisclosureRequest = CloudApprovalPreviewDisclosureRequest()
    approved: bool = False
    explicit_confirmed: bool = False


class CloudApprovalPreviewResponse(BaseModel):
    """Offline preview of a cloud approval request — no provider or network access."""

    provider_id: str
    purpose: str
    scope: str
    explicit_confirmed: bool
    is_approved: bool

    repo_context_included: bool
    diffs_included: bool
    files_included: bool
    data_was_redacted: bool
    secrets_excluded: bool
    full_repo_dump_blocked: bool
    bytes_estimate: int

    approval_status: str
    is_valid: bool
    risk_hints: list[str]


class CloudConfigPreviewResponse(BaseModel):
    """Disabled offline cloud configuration metadata without runtime authority."""

    provider_id: str
    enabled: Literal[False]
    status: Literal["disabled", "not_configured"]
    transport_kind: Literal["remote_http"]
    remote_http_allowed: Literal[False]
    requires_explicit_approval: Literal[True]
    approval_scope: Literal["one_run_only"]
    secrets_source: Literal["not_configured", "env_reference_only"]
    secrets_loaded: Literal[False]
    endpoint_configured: Literal[False]
    execution_allowed: Literal[False]
    config_source: Literal["static/offline/default"]
    cloud_execution: Literal["No"]


class ModelJobResponse(BaseModel):
    """Prompt-free lifecycle snapshot for one bounded model job."""

    job_id: UUID
    adapter_id: str
    capability: Literal["chat", "coding"]
    state: Literal["queued", "running", "cancelling", "succeeded", "failed", "cancelled"]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    result: LocalModelCompletionResponse | None
    error: str | None


class CodeEditPreviewRequest(BaseModel):
    """Read-only file content proposal for approval-bound local code edits."""

    path: str = Field(min_length=1, max_length=500)
    new_content: str = Field(min_length=1, max_length=100_000)
    operation: Literal["update"] = "update"
    model_response: str | None = Field(default=None, max_length=0)


class CodeEditApproveRequest(BaseModel):
    """Exact proposal-hash-bound human approval for one change set."""

    change_set_id: UUID
    proposal_hash: str = Field(min_length=1, max_length=128)
    approved: Literal[True]


class CodeEditApplyRequest(BaseModel):
    """Exact proposal-hash-bound confirmation for one approved change set."""

    change_set_id: UUID
    proposal_hash: str = Field(min_length=1, max_length=128)
    confirmed: Literal[True]


class FileChangeResponse(BaseModel):
    """One safe, reviewable file change without before/after content."""

    path: str
    operation: str
    diff: str


class CodeEditPreviewResponse(BaseModel):
    """Non-executable change-set preview with approval requirement."""

    change_set_id: UUID
    proposal_hash: str
    status: str
    approval_required: Literal[True]
    diff: str
    shell_executed: Literal[False]
    git_executed: Literal[False]
    network_used: Literal[False]
    model_authority: Literal[False]


class CapabilityEntryResponse(BaseModel):
    """One capability's policy mode and execution decision."""

    name: str
    mode: str
    decision_for_execution: str
    requires_approval: bool
    preview_only: bool
    disabled: bool


class CapabilityPreviewResponse(BaseModel):
    """Read-only capability policy metadata — never activates anything."""

    policy_version: Literal["1.0.0"]
    capabilities: list[CapabilityEntryResponse]
    shell_executed: Literal[False]
    git_executed: Literal[False]
    network_used: Literal[False]
    cloud_used: Literal[False]
    model_called: Literal[False]
    runtime_activated: Literal[False]


class CodeEditApplyResponse(BaseModel):
    """Applied change-set confirmation without tool authority."""

    change_set_id: UUID
    proposal_hash: str
    status: str
    shell_executed: Literal[False]
    git_executed: Literal[False]
    network_used: Literal[False]
    model_authority: Literal[False]


class TestRunPreviewRequest(BaseModel):
    """Request to preview an allowlisted test command."""

    command_id: str = Field(min_length=1, max_length=64)


class TestRunPreviewResponse(BaseModel):
    """Read-only preview of an allowlisted test run."""

    test_run_id: UUID
    command_id: str
    display_name: str
    command_args: list[str]
    capability: Literal["run_tests"]
    decision: str
    requires_approval: Literal[True]
    approval_hash: str
    shell_used: Literal[False]
    git_used: Literal[False]
    network_used: Literal[False]
    cloud_used: Literal[False]
    model_called: Literal[False]


class TestRunApproveRequest(BaseModel):
    """Explicit human approval for one test run."""

    test_run_id: UUID
    approval_hash: str = Field(min_length=1, max_length=128)
    approved: Literal[True]


class TestRunApproveResponse(BaseModel):
    """Confirmation that the test run was approved."""

    status: Literal["approved"]
    test_run_id: UUID


class TestRunExecuteRequest(BaseModel):
    """Explicit confirmed request to execute one approved test run."""

    test_run_id: UUID
    approval_hash: str = Field(min_length=1, max_length=128)
    confirmed: Literal[True]


class TestRunExecuteResponse(BaseModel):
    """Bounded result from one executed test run."""

    test_run_id: UUID
    command_id: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    output_truncated: bool
    error: str | None
    shell_used: Literal[False]
    git_used: Literal[False]
    network_used: Literal[False]
    cloud_used: Literal[False]
    model_called: Literal[False]
