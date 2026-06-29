"""Prepare, approve, and apply exact sets of guarded file changes."""

import hashlib
import hmac
import json
from dataclasses import replace
from datetime import UTC, datetime
from difflib import unified_diff
from threading import RLock
from uuid import UUID, uuid4

from sagent_agent_core.models import (
    ChangeOperation,
    ChangeRequest,
    ChangeSet,
    ChangeSetStatus,
    FileChange,
)
from sagent_tools import FileTool


class ChangeSetNotFoundError(KeyError):
    """Raised when a requested change set is unknown."""


class ApprovalError(ValueError):
    """Raised when approval is missing, stale, or targets another proposal."""


class ChangeConflictError(ValueError):
    """Raised when the workspace changed after proposal preparation."""


class ChangeSetService:
    """In-memory lifecycle manager for content-bound file proposals."""

    def __init__(self, file_tool: FileTool, *, max_changes: int = 100) -> None:
        if max_changes < 1:
            raise ValueError("max_changes must be positive.")
        self.file_tool = file_tool
        self.max_changes = max_changes
        self._change_sets: dict[UUID, ChangeSet] = {}
        self._lock = RLock()

    def prepare(self, requests: list[ChangeRequest]) -> ChangeSet:
        """Inspect before states and create a stable, reviewable proposal."""

        if not requests:
            raise ValueError("At least one file change is required.")
        if len(requests) > self.max_changes:
            raise ValueError("Change set exceeds the configured file limit.")

        changes: list[FileChange] = []
        resolved_targets: set[str] = set()
        for request in requests:
            self.file_tool._validate_content(request.new_content)
            resolved = self.file_tool.guard.resolve(
                request.path,
                must_exist=request.operation is ChangeOperation.UPDATE,
            )
            canonical_path = self.file_tool.guard.relative_path(resolved)
            identity = str(resolved)
            if identity in resolved_targets:
                raise ValueError("A change set cannot target the same file twice.")
            resolved_targets.add(identity)

            if request.operation is ChangeOperation.CREATE:
                if resolved.exists():
                    raise ChangeConflictError("Create target already exists.")
                if not resolved.parent.is_dir():
                    raise ChangeConflictError("Parent directory must already exist.")
                old_content = None
            else:
                old_content = self.file_tool.read_file(canonical_path)

            old_sha256 = self._hash_content(old_content) if old_content is not None else None
            new_sha256 = self._hash_content(request.new_content)
            changes.append(
                FileChange(
                    path=canonical_path,
                    operation=request.operation,
                    old_content=old_content,
                    new_content=request.new_content,
                    old_sha256=old_sha256,
                    new_sha256=new_sha256,
                    diff=self._make_diff(
                        canonical_path,
                        request.operation,
                        old_content,
                        request.new_content,
                    ),
                )
            )

        frozen_changes = tuple(changes)
        change_set = ChangeSet(
            change_set_id=uuid4(),
            changes=frozen_changes,
            proposal_hash=self._proposal_hash(frozen_changes),
            status=ChangeSetStatus.PREPARED,
            created_at=datetime.now(UTC),
        )
        with self._lock:
            self._change_sets[change_set.change_set_id] = change_set
        return change_set

    def get(self, change_set_id: UUID) -> ChangeSet:
        """Return an immutable proposal snapshot."""

        with self._lock:
            try:
                return self._change_sets[change_set_id]
            except KeyError as error:
                raise ChangeSetNotFoundError(change_set_id) from error

    def approve(self, change_set_id: UUID, expected_hash: str) -> ChangeSet:
        """Approve exactly the previously displayed proposal hash."""

        with self._lock:
            change_set = self.get(change_set_id)
            if change_set.status is not ChangeSetStatus.PREPARED:
                raise ApprovalError(f"Change set is already {change_set.status.value}.")
            self._verify_hash(change_set, expected_hash)
            approved = replace(
                change_set,
                status=ChangeSetStatus.APPROVED,
                approved_at=datetime.now(UTC),
            )
            self._change_sets[change_set_id] = approved
            return approved

    def apply(self, change_set_id: UUID, expected_hash: str) -> ChangeSet:
        """Revalidate the workspace and apply an exactly approved proposal once."""

        with self._lock:
            change_set = self.get(change_set_id)
            if change_set.status is not ChangeSetStatus.APPROVED:
                raise ApprovalError("Change set must be approved before it can be applied.")
            self._verify_hash(change_set, expected_hash)
            self._assert_workspace_unchanged(change_set)

            for change in change_set.changes:
                receipt = self.file_tool._issue_receipt(
                    change_set_id=change_set.change_set_id,
                    proposal_hash=change_set.proposal_hash,
                    path=change.path,
                    operation=change.operation.value,
                    content=change.new_content,
                )
                if change.operation is ChangeOperation.CREATE:
                    self.file_tool.create_file(change.path, change.new_content, receipt)
                else:
                    self.file_tool.write_file(change.path, change.new_content, receipt)

            applied = replace(
                change_set,
                status=ChangeSetStatus.APPLIED,
                applied_at=datetime.now(UTC),
            )
            self._change_sets[change_set_id] = applied
            return applied

    def _assert_workspace_unchanged(self, change_set: ChangeSet) -> None:
        for change in change_set.changes:
            resolved = self.file_tool.guard.resolve(change.path)
            if change.operation is ChangeOperation.CREATE:
                if resolved.exists():
                    raise ChangeConflictError(
                        f"Workspace changed after preparation: {change.path} now exists."
                    )
                continue
            try:
                current = self.file_tool.read_file(change.path)
            except (OSError, ValueError) as error:
                raise ChangeConflictError(
                    f"Workspace changed after preparation: {change.path} is unavailable."
                ) from error
            if not hmac.compare_digest(self._hash_content(current), change.old_sha256 or ""):
                raise ChangeConflictError(
                    f"Workspace changed after preparation: {change.path} has new content."
                )

    @staticmethod
    def _verify_hash(change_set: ChangeSet, expected_hash: str) -> None:
        if not hmac.compare_digest(change_set.proposal_hash, expected_hash):
            raise ApprovalError("Proposal hash does not match the displayed change set.")

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def _proposal_hash(cls, changes: tuple[FileChange, ...]) -> str:
        payload = [
            {
                "new_sha256": change.new_sha256,
                "old_sha256": change.old_sha256,
                "operation": change.operation.value,
                "path": change.path,
            }
            for change in changes
        ]
        canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _make_diff(
        path: str,
        operation: ChangeOperation,
        old_content: str | None,
        new_content: str,
    ) -> str:
        old_lines = [] if old_content is None else old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        return "".join(
            unified_diff(
                old_lines,
                new_lines,
                fromfile="/dev/null" if operation is ChangeOperation.CREATE else f"a/{path}",
                tofile=f"b/{path}",
            )
        )
