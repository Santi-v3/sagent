"""Server-owned test profiles for the Sagent monorepo."""

import shutil
import sys
from pathlib import Path

from sagent_tools.runner import TestProfile, TestRunner
from sagent_tools.workspace import WorkspaceGuard


def create_default_test_runner(workspace_root: str | Path) -> TestRunner:
    """Build the fixed local allowlist without accepting request-controlled argv."""

    # Keep the virtual-environment entry point instead of resolving its base-Python symlink.
    python = str(Path(sys.executable).absolute())
    profiles = [
        TestProfile(
            profile_id="project-tests",
            command="python -m pytest -q -p no:cacheprovider",
            argv=(python, "-m", "pytest", "-q", "-p", "no:cacheprovider"),
            timeout_seconds=120,
        ),
        TestProfile(
            profile_id="python-lint",
            command="python -m ruff check apps/agent-api packages",
            argv=(python, "-m", "ruff", "check", "apps/agent-api", "packages"),
            timeout_seconds=60,
        ),
    ]

    node = shutil.which("node")
    eslint_cli = Path(workspace_root) / "apps/web/node_modules/eslint/bin/eslint.js"
    if node and eslint_cli.is_file():
        profiles.append(
            TestProfile(
                profile_id="web-lint",
                command="node node_modules/eslint/bin/eslint.js .",
                argv=(str(Path(node).absolute()), str(eslint_cli.resolve()), "."),
                working_directory="apps/web",
                timeout_seconds=120,
            )
        )

    return TestRunner(WorkspaceGuard(workspace_root), profiles)
