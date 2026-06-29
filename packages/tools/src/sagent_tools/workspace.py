"""Canonical workspace boundary and sensitive-path policy."""

import re
from pathlib import Path


class WorkspaceSecurityError(ValueError):
    """Raised when a requested path violates the workspace policy."""


class WorkspaceGuard:
    """Resolve untrusted relative paths without allowing workspace escape."""

    _SENSITIVE_NAMES = frozenset(
        {
            ".env",
            ".netrc",
            ".npmrc",
            ".pypirc",
            "authorized_keys",
            "credentials",
            "credentials.json",
            "id_dsa",
            "id_ecdsa",
            "id_ed25519",
            "id_rsa",
            "known_hosts",
            "service-account.json",
            "token",
            "token.json",
        }
    )
    _SENSITIVE_DIRECTORIES = frozenset({".aws", ".gnupg", ".ssh"})
    _SENSITIVE_SUFFIXES = frozenset({".key", ".p12", ".pem", ".pfx"})
    _SENSITIVE_WORD = re.compile(r"(^|[._-])(credential|secret|token)([._-]|$)")

    def __init__(self, root: str | Path) -> None:
        candidate = Path(root).expanduser()
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as error:
            raise WorkspaceSecurityError("Workspace root does not exist.") from error
        if not resolved.is_dir():
            raise WorkspaceSecurityError("Workspace root must be a directory.")
        self._root = resolved

    @property
    def root(self) -> Path:
        """Return the fixed canonical workspace root."""

        return self._root

    def resolve(self, untrusted_path: str | Path, *, must_exist: bool = False) -> Path:
        """Validate and resolve a path inside the fixed workspace root."""

        raw = str(untrusted_path)
        if not raw or "\x00" in raw:
            raise WorkspaceSecurityError("Path must be non-empty and contain no NUL bytes.")

        relative = Path(raw)
        if relative.is_absolute():
            raise WorkspaceSecurityError("Absolute paths are not allowed.")
        if ".." in relative.parts:
            raise WorkspaceSecurityError("Path traversal is not allowed.")

        self._assert_not_sensitive(relative.parts)
        candidate = self._root.joinpath(relative)
        try:
            resolved = candidate.resolve(strict=must_exist)
        except OSError as error:
            raise WorkspaceSecurityError("Requested path does not exist.") from error
        self._assert_inside_workspace(resolved)

        resolved_relative = resolved.relative_to(self._root)
        self._assert_not_sensitive(resolved_relative.parts)
        return resolved

    def relative_path(self, resolved_path: Path) -> str:
        """Return a stable POSIX path after checking the workspace boundary."""

        canonical = resolved_path.resolve(strict=False)
        self._assert_inside_workspace(canonical)
        relative = canonical.relative_to(self._root)
        self._assert_not_sensitive(relative.parts)
        return relative.as_posix()

    def is_sensitive(self, path: str | Path) -> bool:
        """Report whether a relative path is hidden by the sensitive-path policy."""

        try:
            self._assert_not_sensitive(Path(path).parts)
        except WorkspaceSecurityError:
            return True
        return False

    def _assert_inside_workspace(self, path: Path) -> None:
        try:
            path.relative_to(self._root)
        except ValueError as error:
            raise WorkspaceSecurityError("Path escapes the configured workspace.") from error

    def _assert_not_sensitive(self, parts: tuple[str, ...]) -> None:
        for part in parts:
            lowered = part.casefold()
            if lowered in {"", "."}:
                continue
            if lowered in self._SENSITIVE_DIRECTORIES:
                raise WorkspaceSecurityError("Sensitive credential directories are blocked.")
            if lowered in self._SENSITIVE_NAMES or lowered.startswith(".env."):
                raise WorkspaceSecurityError("Sensitive credential files are blocked.")
            if Path(lowered).suffix in self._SENSITIVE_SUFFIXES:
                raise WorkspaceSecurityError("Private key and certificate files are blocked.")
            if self._SENSITIVE_WORD.search(lowered):
                raise WorkspaceSecurityError("Token, secret, and credential files are blocked.")
