"""Single-file local code edits built on the existing guarded ChangeSet lifecycle."""

from functools import lru_cache
from pathlib import Path
from uuid import UUID

from sagent_agent_core import (
    ChangeOperation,
    ChangeRequest,
    ChangeSet,
    ChangeSetService,
)
from sagent_tools import FileTool, WorkspaceGuard, redact_secrets


class CodeEditPolicyError(ValueError):
    """Raised when a proposed code edit is outside the narrow local policy."""


class CodeEditService:
    """Preview, approve, and apply exactly one guarded full-file text update."""

    _BLOCKED_FILENAMES = frozenset(
        {
            "bun.lock",
            "bun.lockb",
            "composer.json",
            "composer.lock",
            "cargo.lock",
            "cargo.toml",
            "gemfile",
            "gemfile.lock",
            "go.mod",
            "go.sum",
            "package-lock.json",
            "package.json",
            "pipfile",
            "pipfile.lock",
            "pnpm-lock.yaml",
            "pnpm-workspace.yaml",
            "poetry.lock",
            "pyproject.toml",
            "requirements.txt",
            "setup.cfg",
            "setup.py",
            "uv.lock",
            "yarn.lock",
        }
    )

    def __init__(self, file_tool: FileTool) -> None:
        self.file_tool = file_tool
        self.change_sets = ChangeSetService(file_tool, max_changes=1)

    def preview(self, path: str, new_content: str) -> ChangeSet:
        """Prepare one full-file update without writing to the workspace."""

        self._validate_policy_path(path)
        resolved = self.file_tool.guard.resolve(path, must_exist=True)
        canonical_path = self.file_tool.guard.relative_path(resolved)
        self._validate_policy_path(canonical_path)
        current_content = self.file_tool.read_file(canonical_path)
        self._reject_secret_content(current_content)
        self._reject_secret_content(new_content)
        if current_content == new_content:
            raise CodeEditPolicyError("The proposed update must change the file content.")
        return self.change_sets.prepare(
            [
                ChangeRequest(
                    path=canonical_path,
                    new_content=new_content,
                    operation=ChangeOperation.UPDATE,
                )
            ]
        )

    def approve(self, change_set_id: UUID, proposal_hash: str) -> ChangeSet:
        """Approve only the exact previously prepared proposal hash."""

        return self.change_sets.approve(change_set_id, proposal_hash)

    def apply(self, change_set_id: UUID, proposal_hash: str) -> ChangeSet:
        """Apply one exact approved proposal after stale-workspace revalidation."""

        return self.change_sets.apply(change_set_id, proposal_hash)

    def _validate_policy_path(self, path: str) -> None:
        relative = Path(path)
        visible_parts = [part for part in relative.parts if part not in {"", "."}]
        if any(part.startswith(".") for part in visible_parts):
            raise CodeEditPolicyError("Hidden files and directories are not editable.")
        if not visible_parts:
            raise CodeEditPolicyError("A visible file path is required.")
        filename = visible_parts[-1].casefold()
        if filename in self._BLOCKED_FILENAMES:
            raise CodeEditPolicyError("Dependency manifests and lockfiles are not editable.")
        if filename.endswith((".lock", ".lockb")):
            raise CodeEditPolicyError("Dependency manifests and lockfiles are not editable.")
        if filename.startswith("requirements") and Path(filename).suffix in {".in", ".txt"}:
            raise CodeEditPolicyError("Dependency manifests and lockfiles are not editable.")

    @staticmethod
    def _reject_secret_content(content: str) -> None:
        if redact_secrets(content)[1]:
            raise CodeEditPolicyError("Potential secret content blocks this code edit.")


@lru_cache(maxsize=1)
def get_code_edit_service() -> CodeEditService:
    """Return one process-local service bound to the repository workspace."""

    workspace_root = Path(__file__).resolve().parents[4]
    return CodeEditService(FileTool(WorkspaceGuard(workspace_root)))
