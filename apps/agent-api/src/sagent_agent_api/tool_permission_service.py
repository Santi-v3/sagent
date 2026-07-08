"""Global tool permission manager singleton for the API."""

from sagent_agent_core import ToolPermissionManager


_manager: ToolPermissionManager | None = None


def get_tool_permission_manager() -> ToolPermissionManager:
    global _manager
    if _manager is None:
        _manager = ToolPermissionManager()
    return _manager


def reset_tool_permission_manager() -> None:
    global _manager
    _manager = None
