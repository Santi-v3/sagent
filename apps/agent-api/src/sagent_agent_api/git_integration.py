"""Lazy construction of the repository-bound Git tool."""

from functools import lru_cache
from pathlib import Path

from sagent_tools import GitTool, WorkspaceGuard


@lru_cache(maxsize=1)
def get_git_tool() -> GitTool:
    """Return one local Git tool bound to the Sagent repository root."""

    workspace_root = Path(__file__).resolve().parents[4]
    return GitTool(WorkspaceGuard(workspace_root))
