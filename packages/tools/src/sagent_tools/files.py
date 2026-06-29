"""Guarded UTF-8 text-file operations with content-bound write receipts."""

import hashlib
import hmac
import os
import secrets
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID

from sagent_tools.workspace import WorkspaceGuard, WorkspaceSecurityError

WriteOperation = Literal["create", "update"]


class FileAccessError(ValueError):
    """Raised when a file does not meet the bounded text-file contract."""


@dataclass(frozen=True, slots=True)
class _WriteReceipt:
    change_set_id: UUID
    proposal_hash: str
    path: str
    operation: WriteOperation
    content_sha256: str
    signature: str


class FileTool:
    """Read safely and write only with a valid, exact approval receipt."""

    def __init__(
        self,
        guard: WorkspaceGuard,
        *,
        max_file_bytes: int = 1_048_576,
        max_list_entries: int = 1_000,
    ) -> None:
        if max_file_bytes < 1 or max_list_entries < 1:
            raise ValueError("Resource limits must be positive.")
        self.guard = guard
        self.max_file_bytes = max_file_bytes
        self.max_list_entries = max_list_entries
        self.__receipt_key = secrets.token_bytes(32)

    def read_file(self, path: str) -> str:
        """Read one allowed, regular UTF-8 text file within the workspace."""

        resolved = self.guard.resolve(path, must_exist=True)
        if not resolved.is_file():
            raise FileAccessError("Only regular files can be read.")
        try:
            size = resolved.stat().st_size
        except OSError as error:
            raise FileAccessError("Could not inspect the requested file.") from error
        if size > self.max_file_bytes:
            raise FileAccessError("File exceeds the configured size limit.")
        try:
            payload = resolved.read_bytes()
        except OSError as error:
            raise FileAccessError("Could not read the requested file.") from error
        if b"\x00" in payload:
            raise FileAccessError("Binary files are not allowed.")
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise FileAccessError("Only UTF-8 text files are allowed.") from error

    def list_files(self, path: str = ".") -> list[str]:
        """List allowed regular files recursively without exposing sensitive paths."""

        directory = self.guard.resolve(path, must_exist=True)
        if not directory.is_dir():
            raise FileAccessError("Only directories can be listed.")

        results: list[str] = []
        inspected = 0
        for candidate in directory.rglob("*"):
            inspected += 1
            if inspected > self.max_list_entries * 4:
                raise FileAccessError("Directory scan exceeds the configured entry limit.")
            try:
                resolved = self.guard.resolve(
                    self.guard.relative_path(candidate),
                    must_exist=True,
                )
            except (OSError, WorkspaceSecurityError, ValueError):
                continue
            if not resolved.is_file():
                continue
            relative = self.guard.relative_path(resolved)
            if relative not in results:
                results.append(relative)
            if len(results) > self.max_list_entries:
                raise FileAccessError("Directory listing exceeds the configured entry limit.")
        return sorted(results)

    def create_file(self, path: str, content: str, receipt: _WriteReceipt) -> None:
        """Create one file atomically after verifying its exact write receipt."""

        self._validate_content(content)
        self._verify_receipt(path, content, "create", receipt)
        target = self.guard.resolve(path)
        if target.exists():
            raise FileAccessError("Create target already exists.")
        if not target.parent.is_dir():
            raise FileAccessError("Parent directory must already exist.")
        self._atomic_create(target, content)

    def write_file(self, path: str, content: str, receipt: _WriteReceipt) -> None:
        """Replace one existing file atomically after exact receipt verification."""

        self._validate_content(content)
        self._verify_receipt(path, content, "update", receipt)
        target = self.guard.resolve(path, must_exist=True)
        if not target.is_file():
            raise FileAccessError("Update target must be a regular file.")
        self._atomic_replace(target, content)

    def _validate_content(self, content: str) -> None:
        if "\x00" in content:
            raise FileAccessError("NUL bytes are not allowed in text files.")
        size = len(content.encode("utf-8"))
        if size > self.max_file_bytes:
            raise FileAccessError("Content exceeds the configured size limit.")

    def _issue_receipt(
        self,
        *,
        change_set_id: UUID,
        proposal_hash: str,
        path: str,
        operation: WriteOperation,
        content: str,
    ) -> _WriteReceipt:
        content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        message = self._receipt_message(
            change_set_id,
            proposal_hash,
            path,
            operation,
            content_sha256,
        )
        signature = hmac.new(self.__receipt_key, message, hashlib.sha256).hexdigest()
        return _WriteReceipt(
            change_set_id=change_set_id,
            proposal_hash=proposal_hash,
            path=path,
            operation=operation,
            content_sha256=content_sha256,
            signature=signature,
        )

    def _verify_receipt(
        self,
        path: str,
        content: str,
        operation: WriteOperation,
        receipt: _WriteReceipt,
    ) -> None:
        content_sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if (
            receipt.path != path
            or receipt.operation != operation
            or not hmac.compare_digest(receipt.content_sha256, content_sha256)
        ):
            raise FileAccessError("Approval receipt does not match the requested write.")
        message = self._receipt_message(
            receipt.change_set_id,
            receipt.proposal_hash,
            receipt.path,
            receipt.operation,
            receipt.content_sha256,
        )
        expected = hmac.new(self.__receipt_key, message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(receipt.signature, expected):
            raise FileAccessError("Approval receipt is invalid.")

    @staticmethod
    def _receipt_message(
        change_set_id: UUID,
        proposal_hash: str,
        path: str,
        operation: WriteOperation,
        content_sha256: str,
    ) -> bytes:
        return "\x1f".join(
            [str(change_set_id), proposal_hash, path, operation, content_sha256]
        ).encode()

    @staticmethod
    def _write_temp(target: Path, content: str, *, mode: int | None = None) -> Path:
        descriptor, temp_name = tempfile.mkstemp(prefix=".sagent-write-", dir=target.parent)
        temp_path = Path(temp_name)
        try:
            if mode is not None:
                os.fchmod(descriptor, mode)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise
        return temp_path

    def _atomic_create(self, target: Path, content: str) -> None:
        temp_path = self._write_temp(target, content)
        try:
            os.link(temp_path, target)
        except FileExistsError as error:
            raise FileAccessError("Create target already exists.") from error
        except OSError as error:
            raise FileAccessError("Could not create the requested file.") from error
        finally:
            temp_path.unlink(missing_ok=True)

    def _atomic_replace(self, target: Path, content: str) -> None:
        mode = stat.S_IMODE(target.stat().st_mode)
        temp_path = self._write_temp(target, content, mode=mode)
        try:
            os.replace(temp_path, target)
        except OSError as error:
            raise FileAccessError("Could not update the requested file.") from error
        finally:
            temp_path.unlink(missing_ok=True)
