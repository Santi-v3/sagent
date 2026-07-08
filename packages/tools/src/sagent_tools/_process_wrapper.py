"""Apply process limits before replacing the process with an allowlisted command."""

import os
import platform
import subprocess
import sys


def _bounded_limit(kind: int, requested: int) -> tuple[int, int]:
    import resource
    _, hard = resource.getrlimit(kind)
    if hard == resource.RLIM_INFINITY:
        return requested, requested
    bounded = min(requested, hard)
    return bounded, bounded


def _set_unix_limits(cpu_seconds: int) -> None:
    import resource
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, _bounded_limit(resource.RLIMIT_NOFILE, 256))
    resource.setrlimit(resource.RLIMIT_CPU, _bounded_limit(resource.RLIMIT_CPU, cpu_seconds))


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(126)
    cpu_seconds = int(sys.argv[1])
    command = sys.argv[2:]

    if platform.system() != "Windows":
        _set_unix_limits(cpu_seconds)
        os.execve(command[0], command, os.environ)  # noqa: S606
    else:
        proc = subprocess.run(command, capture_output=True, timeout=cpu_seconds)
        sys.stdout.buffer.write(proc.stdout)
        sys.stderr.buffer.write(proc.stderr)
        raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
