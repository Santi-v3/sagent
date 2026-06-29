"""Approval and conflict tests for content-bound change sets."""

from pathlib import Path

import pytest

from sagent_agent_core import (
    ApprovalError,
    ChangeConflictError,
    ChangeOperation,
    ChangeRequest,
    ChangeSetService,
    ChangeSetStatus,
    FileTool,
    WorkspaceGuard,
    WorkspaceSecurityError,
)


def make_service(workspace: Path) -> ChangeSetService:
    return ChangeSetService(FileTool(WorkspaceGuard(workspace)))


def test_change_is_not_written_before_exact_approval(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("before\n", encoding="utf-8")
    service = make_service(tmp_path)
    change_set = service.prepare([ChangeRequest("README.md", "after\n", ChangeOperation.UPDATE)])

    with pytest.raises(ApprovalError, match="approved"):
        service.apply(change_set.change_set_id, change_set.proposal_hash)

    assert target.read_text(encoding="utf-8") == "before\n"


def test_normal_update_after_approval_succeeds_and_has_diff(tmp_path: Path) -> None:
    target = tmp_path / "README.md"
    target.write_text("before\n", encoding="utf-8")
    service = make_service(tmp_path)
    prepared = service.prepare([ChangeRequest("README.md", "after\n", ChangeOperation.UPDATE)])

    assert prepared.status is ChangeSetStatus.PREPARED
    assert prepared.changes[0].old_content == "before\n"
    assert prepared.changes[0].new_content == "after\n"
    assert "--- a/README.md" in prepared.changes[0].diff
    assert "+++ b/README.md" in prepared.changes[0].diff
    assert "-before" in prepared.changes[0].diff
    assert "+after" in prepared.changes[0].diff

    approved = service.approve(prepared.change_set_id, prepared.proposal_hash)
    applied = service.apply(approved.change_set_id, approved.proposal_hash)

    assert approved.status is ChangeSetStatus.APPROVED
    assert applied.status is ChangeSetStatus.APPLIED
    assert applied.approved_at is not None
    assert applied.applied_at is not None
    assert target.read_text(encoding="utf-8") == "after\n"


def test_normal_create_after_approval_succeeds(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    service = make_service(tmp_path)
    prepared = service.prepare([ChangeRequest("docs/new.md", "new\n", ChangeOperation.CREATE)])

    assert prepared.changes[0].old_content is None
    assert "--- /dev/null" in prepared.changes[0].diff
    service.approve(prepared.change_set_id, prepared.proposal_hash)
    service.apply(prepared.change_set_id, prepared.proposal_hash)

    assert (tmp_path / "docs" / "new.md").read_text(encoding="utf-8") == "new\n"


def test_wrong_proposal_hash_cannot_approve_or_apply(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("before", encoding="utf-8")
    service = make_service(tmp_path)
    prepared = service.prepare([ChangeRequest("file.txt", "after", ChangeOperation.UPDATE)])

    with pytest.raises(ApprovalError, match="hash"):
        service.approve(prepared.change_set_id, "0" * 64)
    service.approve(prepared.change_set_id, prepared.proposal_hash)
    with pytest.raises(ApprovalError, match="hash"):
        service.apply(prepared.change_set_id, "f" * 64)

    assert (tmp_path / "file.txt").read_text(encoding="utf-8") == "before"


def test_stale_workspace_blocks_approved_update(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("before", encoding="utf-8")
    service = make_service(tmp_path)
    prepared = service.prepare([ChangeRequest("file.txt", "after", ChangeOperation.UPDATE)])
    service.approve(prepared.change_set_id, prepared.proposal_hash)
    target.write_text("changed by someone else", encoding="utf-8")

    with pytest.raises(ChangeConflictError, match="new content"):
        service.apply(prepared.change_set_id, prepared.proposal_hash)

    assert target.read_text(encoding="utf-8") == "changed by someone else"


def test_stale_workspace_blocks_approved_create(tmp_path: Path) -> None:
    service = make_service(tmp_path)
    prepared = service.prepare([ChangeRequest("new.txt", "agent", ChangeOperation.CREATE)])
    service.approve(prepared.change_set_id, prepared.proposal_hash)
    (tmp_path / "new.txt").write_text("human", encoding="utf-8")

    with pytest.raises(ChangeConflictError, match="now exists"):
        service.apply(prepared.change_set_id, prepared.proposal_hash)

    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "human"


def test_sensitive_file_cannot_be_prepared_or_overwritten(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("TOKEN=original", encoding="utf-8")
    service = make_service(tmp_path)

    with pytest.raises(WorkspaceSecurityError, match="blocked"):
        service.prepare([ChangeRequest(".env", "TOKEN=replaced", ChangeOperation.UPDATE)])

    assert (tmp_path / ".env").read_text(encoding="utf-8") == "TOKEN=original"


def test_duplicate_target_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("before", encoding="utf-8")
    service = make_service(tmp_path)

    with pytest.raises(ValueError, match="same file twice"):
        service.prepare(
            [
                ChangeRequest("file.txt", "one", ChangeOperation.UPDATE),
                ChangeRequest("./file.txt", "two", ChangeOperation.UPDATE),
            ]
        )


def test_applied_change_set_cannot_be_reused(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("before", encoding="utf-8")
    service = make_service(tmp_path)
    prepared = service.prepare([ChangeRequest("file.txt", "after", ChangeOperation.UPDATE)])
    service.approve(prepared.change_set_id, prepared.proposal_hash)
    service.apply(prepared.change_set_id, prepared.proposal_hash)

    with pytest.raises(ApprovalError, match="approved"):
        service.apply(prepared.change_set_id, prepared.proposal_hash)
