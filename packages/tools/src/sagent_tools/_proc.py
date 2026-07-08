"""Cross-platform subprocess utilities."""

import os
import platform
import signal
import sys


def is_windows() -> bool:
    return platform.system() == "Windows"


def kill_process_group(process: "subprocess.Popen[bytes]") -> None:  # type: ignore[name-defined]
    """Kill a process and its children cross-platform."""
    if is_windows():
        process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def create_process_kwargs() -> dict:
    """Return extra Popen kwargs for process group management."""
    if is_windows():
        return {}
    return {"start_new_session": True}
