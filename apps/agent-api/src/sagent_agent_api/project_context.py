import json
import os
import subprocess
from pathlib import Path


def _find_project_root(start: str | None = None) -> str | None:
    """Find the project root by looking for .git or project files upward."""
    path = Path(start or os.getcwd()).resolve()
    markers = {".git", "README.md", "package.json", "pyproject.toml", "Cargo.toml", "go.mod"}
    for parent in [path] + list(path.parents):
        if any((parent / m).exists() for m in markers):
            return str(parent)
    return None


def _safe_read(path: str, max_chars: int = 8000) -> str | None:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
    except Exception:
        return None


def _git_log(project_root: str, max_lines: int = 15) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={max_lines}", "--oneline", "--no-decorate"],
            capture_output=True, text=True, timeout=5, cwd=project_root,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def _git_branch(project_root: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=3, cwd=project_root,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _git_remote(project_root: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=3, cwd=project_root,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def collect_project_context(start: str | None = None) -> dict:
    """Collect project context files and metadata."""
    root = _find_project_root(start)
    if not root:
        return {"root": None, "context": "", "files_loaded": 0}

    files_to_read = [
        "README.md", "README",
        "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
        "Makefile", ".env.example",
        ".cursorrules", ".clinerules",
    ]

    loaded = {}
    for fname in files_to_read:
        fpath = os.path.join(root, fname)
        if os.path.isfile(fpath):
            content = _safe_read(fpath)
            if content:
                loaded[fname] = content

    git_log_str = _git_log(root)
    branch = _git_branch(root)
    remote = _git_remote(root)

    # Build context string
    parts = [f"Project root: {root}"]

    if branch:
        parts.append(f"Git branch: {branch}")
    if remote:
        parts.append(f"Git remote: {remote}")

    for fname, content in loaded.items():
        label = f"Contents of {fname}:"
        parts.append(f"\n=== {label} ===\n{content}")

    if git_log_str:
        parts.append(f"\n=== Recent git log ===\n{git_log_str}")

    return {
        "root": root,
        "context": "\n".join(parts),
        "files_loaded": len(loaded),
        "git_branch": branch,
        "git_remote": remote,
        "recent_commits": git_log_str,
    }
