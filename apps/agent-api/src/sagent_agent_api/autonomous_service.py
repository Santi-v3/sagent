"""Autonomous mode – background project scanning and proactive suggestions."""

import json
import os
import platform
import subprocess
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread
from typing import Any


@dataclass
class Suggestion:
    id: str
    type: str  # git, tests, todos, deps, general
    severity: str  # info, warning, critical
    title: str
    description: str
    command: str  # Suggested command to fix/resolve
    created_at: float
    dismissed: bool = False


@dataclass
class ScanResult:
    timestamp: float
    suggestions: list[Suggestion] = field(default_factory=list)
    duration_ms: int = 0


def _run_git_status(workspace_root: str) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
            cwd=workspace_root,
        )
        if r.returncode != 0:
            return suggestions
        lines = [l for l in r.stdout.split("\n") if l.strip()]
        if lines:
            modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M "))
            untracked = sum(1 for l in lines if l.startswith("?"))
            staged = sum(1 for l in lines if l.startswith("A ") or l.startswith("M ") and not l.startswith(" M"))
            if staged > 0 or modified > 0 or untracked > 0:
                suggestions.append(Suggestion(
                    id=uuid.uuid4().hex[:12],
                    type="git",
                    severity="info",
                    title=f"{staged + modified + untracked} uncommitted changes",
                    description=f"{staged} staged, {modified} modified, {untracked} untracked",
                    command="git add -A && git commit -m 'WIP'",
                    created_at=time.time(),
                ))
        # Check for unpushed commits
        r2 = subprocess.run(
            ["git", "log", "--oneline", "@{u}..HEAD", "--count"],
            capture_output=True, text=True, timeout=10,
            cwd=workspace_root,
        )
        if r2.returncode == 0 and r2.stdout.strip().isdigit():
            count = int(r2.stdout.strip())
            if count > 0:
                suggestions.append(Suggestion(
                    id=uuid.uuid4().hex[:12],
                    type="git",
                    severity="info",
                    title=f"{count} unpushed commit{'s' if count > 1 else ''}",
                    description="Changes are committed but not pushed to remote",
                    command="git push",
                    created_at=time.time(),
                ))
    except Exception:  # noqa: S110
        pass
    return suggestions


def _grep_files(pattern: str, root: str) -> list[str]:
    """Cross-platform grep for TODO/FIXME markers."""
    if platform.system() == "Windows":
        result = []
        for ext in (".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java"):
            for p in Path(root).rglob(f"*{ext}"):
                if not p.is_file():
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                    if any(kw in text for kw in ["TODO", "FIXME", "HACK", "XXX"]):
                        result.append(str(p))
                except Exception:
                    pass
        return result
    else:
        r = subprocess.run(
            ["grep", "-rn", "--include=" + "*.py", "--include=" + "*.ts", "--include=" + "*.tsx",
             "--include=" + "*.js", "--include=" + "*.jsx", "--include=" + "*.rs",
             "--include=" + "*.go", "--include=" + "*.java",
             "-l", "TODO\\|FIXME\\|HACK\\|XXX", root],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return [l.strip() for l in r.stdout.split("\n") if l.strip()]
        return []


def _run_todo_scan(workspace_root: str) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    try:
        files = _grep_files("TODO|FIXME|HACK|XXX", workspace_root)
        if len(files) > 0:
                suggestions.append(Suggestion(
                    id=uuid.uuid4().hex[:12],
                    type="todos",
                    severity="info",
                    title=f"{len(files)} files with TODO/FIXME markers",
                    description=f"Found in: {', '.join(Path(f).name for f in files[:5])}" + ("..." if len(files) > 5 else ""),
                    command="",
                    created_at=time.time(),
                ))
    except Exception:  # noqa: S110
        pass
    return suggestions


def _run_test_check(workspace_root: str) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    # Check if there are test files and if the last run failed
    test_files = list(Path(workspace_root).rglob("*test*.py")) + list(Path(workspace_root).rglob("*spec*.ts"))
    if not test_files:
        return suggestions
    # Quick check for recent test output artifacts
    for marker in [".pytest_cache", "node_modules/.cache"]:
        p = Path(workspace_root) / marker
        if p.exists():
            break
    else:
        # No test cache found, just note that tests exist
        suggestions.append(Suggestion(
            id=uuid.uuid4().hex[:12],
            type="tests",
            severity="info",
            title=f"{len(test_files)} test files found",
            description="Tests are available but haven't been run recently",
            command="",
            created_at=time.time(),
        ))
    return suggestions


def _run_dep_check(workspace_root: str) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    # Check for outdated pip packages
    req_files = list(Path(workspace_root).glob("requirements*.txt")) + list(Path(workspace_root).glob("pyproject.toml"))
    if req_files:
        try:
            r = subprocess.run(
                ["pip", "list", "--outdated", "--format=columns"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                lines = [l for l in r.stdout.split("\n") if l.strip() and not l.startswith("Package") and not l.startswith("---")]
                if len(lines) > 1:  # header + at least one package
                    suggestions.append(Suggestion(
                        id=uuid.uuid4().hex[:12],
                        type="deps",
                        severity="info",
                        title=f"{len(lines) - 1} outdated pip package{'s' if len(lines) > 2 else ''}",
                        description="Some Python dependencies have newer versions",
                        command="pip install --upgrade " + lines[1].split()[0] if len(lines) > 1 else "",
                        created_at=time.time(),
                    ))
        except Exception:  # noqa: S110
            pass
    return suggestions


_DEFAULT_SCANNERS: list[Callable[[str], list[Suggestion]]] = [
    _run_git_status,
    _run_todo_scan,
    _run_test_check,
    _run_dep_check,
]


class AutonomousService:
    """Background service that periodically scans the workspace for actionable insights."""

    def __init__(self, workspace_root: str, interval_seconds: int = 300) -> None:
        self._workspace_root = workspace_root
        self._interval = interval_seconds
        self._enabled = False
        self._thread: Thread | None = None
        self._stop = False
        self._lock = Lock()
        self._last_scan: ScanResult | None = None
        self._suggestions: list[Suggestion] = []
        self._scanners = list(_DEFAULT_SCANNERS)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value
        if value and not self._thread:
            self._stop = False
            self._thread = Thread(target=self._run_loop, daemon=True)
            self._thread.start()
        elif not value:
            self._stop = True
            if self._thread:
                self._thread.join(timeout=5)
                self._thread = None

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": self._enabled,
                "interval": self._interval,
                "last_scan": {
                    "timestamp": self._last_scan.timestamp if self._last_scan else None,
                    "suggestions": len(self._last_scan.suggestions) if self._last_scan else 0,
                    "duration_ms": self._last_scan.duration_ms if self._last_scan else 0,
                } if self._last_scan else None,
                "active_suggestions": len([s for s in self._suggestions if not s.dismissed]),
            }

    def get_suggestions(self, include_dismissed: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            items = self._suggestions if include_dismissed else [s for s in self._suggestions if not s.dismissed]
            return [
                {
                    "id": s.id,
                    "type": s.type,
                    "severity": s.severity,
                    "title": s.title,
                    "description": s.description,
                    "command": s.command,
                    "created_at": s.created_at,
                    "dismissed": s.dismissed,
                }
                for s in items
            ]

    def dismiss_suggestion(self, suggestion_id: str) -> bool:
        with self._lock:
            for s in self._suggestions:
                if s.id == suggestion_id:
                    s.dismissed = True
                    return True
            return False

    def dismiss_all(self) -> None:
        with self._lock:
            for s in self._suggestions:
                s.dismissed = True

    def run_scan_now(self) -> ScanResult:
        t0 = time.time()
        all_suggestions: list[Suggestion] = []
        for scanner in self._scanners:
            try:
                all_suggestions.extend(scanner(self._workspace_root))
            except Exception:  # noqa: S110
                pass
        result = ScanResult(
            timestamp=time.time(),
            suggestions=all_suggestions,
            duration_ms=int((time.time() - t0) * 1000),
        )
        with self._lock:
            self._last_scan = result
            # Merge new suggestions (avoid duplicates by type+title)
            existing_keys = {(s.type, s.title) for s in self._suggestions if not s.dismissed}
            for new_s in result.suggestions:
                if (new_s.type, new_s.title) not in existing_keys:
                    self._suggestions.append(new_s)
                    existing_keys.add((new_s.type, new_s.title))
            # Keep max 50
            if len(self._suggestions) > 50:
                self._suggestions = self._suggestions[-50:]
        return result

    def _run_loop(self) -> None:
        while not self._stop:
            try:
                self.run_scan_now()
            except Exception:  # noqa: S110
                pass
            # Sleep in small increments so we can stop quickly
            for _ in range(self._interval * 10):
                if self._stop:
                    return
                time.sleep(0.1)

    def set_interval(self, seconds: int) -> None:
        self._interval = max(30, min(seconds, 3600))

    def register_scanner(self, scanner: Callable[[str], list[Suggestion]]) -> None:
        self._scanners.append(scanner)


# Singleton
_service: AutonomousService | None = None


def get_autonomous_service(workspace_root: str | None = None) -> AutonomousService:
    global _service
    if _service is None:
        root = workspace_root or os.environ.get("SAGENT_WORKSPACE", str(Path.cwd()))
        _service = AutonomousService(root)
    return _service


def close_autonomous_service() -> None:
    global _service
    if _service:
        _service.set_enabled(False)
        _service = None
