import json
import os
import time
from pathlib import Path
from typing import Any


class RollbackEntry:
    __slots__ = ("tool_name", "args", "timestamp", "undo_info")

    def __init__(self, tool_name: str, args: dict, undo_info: dict | None = None):
        self.tool_name = tool_name
        self.args = args
        self.timestamp = time.time()
        self.undo_info = undo_info or {}


class RollbackManager:
    """Stores undo information for tool calls to enable rollback."""

    def __init__(self):
        self._history: list[RollbackEntry] = []
        self._file_backups: dict[str, str | None] = {}

    def record(self, tool_name: str, args: dict) -> None:
        """Record a tool call and capture undo info."""
        entry = RollbackEntry(tool_name, args)

        if tool_name in ("write_file", "edit_file"):
            path = args.get("path", "")
            if path and os.path.isfile(path):
                with open(path, encoding="utf-8", errors="replace") as f:
                    self._file_backups[path] = f.read()
                entry.undo_info = {"file_backup_path": path}
            elif path:
                self._file_backups[path] = None
                entry.undo_info = {"file_backup_path": path, "was_new": True}

        if tool_name == "git_commit":
            entry.undo_info = {"type": "git_commit", "message": args.get("message", "")}

        self._history.append(entry)

    def rollback_last(self) -> str:
        """Rollback the most recent recorded tool call."""
        if not self._history:
            return json.dumps({"status": "error", "message": "Nothing to rollback."})
        return self._rollback_entry(self._history.pop())

    def rollback_to(self, index: int) -> str:
        """Rollback all calls from index to end."""
        if index < 0 or index >= len(self._history):
            return json.dumps({"status": "error", "message": f"Invalid index {index}."})
        results = []
        for _ in range(len(self._history) - index):
            results.append(self._rollback_entry(self._history.pop()))
        return json.dumps({"status": "ok", "rolled_back": len(results), "details": results})

    def _rollback_entry(self, entry: RollbackEntry) -> dict:
        undo = entry.undo_info or {}
        if entry.tool_name in ("write_file", "edit_file"):
            path = undo.get("file_backup_path", "")
            if path in self._file_backups:
                backup = self._file_backups[path]
                if backup is None:
                    if os.path.isfile(path):
                        os.remove(path)
                    return {"tool": entry.tool_name, "action": "deleted", "path": path}
                with open(path, "w", encoding="utf-8") as f:
                    f.write(backup)
                return {"tool": entry.tool_name, "action": "restored", "path": path}

        if entry.tool_name == "git_commit":
            return {"tool": "git_commit", "action": "requires_manual_revert",
                    "hint": f"Run `git reset --soft HEAD~1` to undo '{undo.get('message', '')}'"}

        return {"tool": entry.tool_name, "action": "no_undo_available"}

    def history_summary(self) -> list[dict[str, Any]]:
        return [
            {"tool_name": e.tool_name, "args": json.dumps(e.args, ensure_ascii=False)[:120],
             "timestamp": e.timestamp, "undo_info": e.undo_info}
            for e in self._history
        ]

    def clear(self) -> None:
        self._history.clear()
        self._file_backups.clear()
