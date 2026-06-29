"""Apply Unix resource limits before replacing the process with an allowlisted command."""

import os
import resource
import sys


def _bounded_limit(kind: int, requested: int) -> tuple[int, int]:
    _, hard = resource.getrlimit(kind)
    if hard == resource.RLIM_INFINITY:
        return requested, requested
    bounded = min(requested, hard)
    return bounded, bounded


def main() -> None:
    """Set fixed limits and execute argv supplied only by the trusted TestRunner."""

    if len(sys.argv) < 3:
        raise SystemExit(126)
    cpu_seconds = int(sys.argv[1])
    command = sys.argv[2:]

    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, _bounded_limit(resource.RLIMIT_NOFILE, 256))
    resource.setrlimit(resource.RLIMIT_CPU, _bounded_limit(resource.RLIMIT_CPU, cpu_seconds))
    os.execve(command[0], command, os.environ)  # noqa: S606 - exact server allowlist argv.


if __name__ == "__main__":
    main()
