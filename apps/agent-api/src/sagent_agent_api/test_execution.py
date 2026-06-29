"""Lazy construction of the local allowlisted test runner."""

from functools import lru_cache
from pathlib import Path

from sagent_tools import TestRunner
from sagent_tools.default_test_profiles import create_default_test_runner


@lru_cache(maxsize=1)
def get_test_runner() -> TestRunner:
    """Return one process-local runner bound to the Sagent repository root."""

    workspace_root = Path(__file__).resolve().parents[4]
    return create_default_test_runner(workspace_root)
