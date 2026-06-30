"""Offline contract checks between Python benchmark policy and static web metadata."""

import json
import re
from pathlib import Path

from sagent_agent_api.model_integration import _LOCAL_PROVIDERS
from sagent_agent_core import SYNTHETIC_BENCHMARK_TASKS

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPOSITORY_ROOT / "apps" / "web"
METADATA_PATH = WEB_ROOT / "data" / "benchmark-status.json"
COMPONENT_PATH = WEB_ROOT / "components" / "benchmark-status.tsx"


def load_ui_metadata() -> dict[str, object]:
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


def test_ui_provider_profiles_match_python_loopback_policy() -> None:
    metadata = load_ui_metadata()
    ui_profiles = {
        profile["name"]: profile["endpoint"] for profile in metadata["providers"]
    }

    assert _LOCAL_PROVIDERS == {"lm-studio": 1_234, "ollama": 11_434}
    assert ui_profiles == {
        "LM Studio": f"127.0.0.1:{_LOCAL_PROVIDERS['lm-studio']}",
        "Ollama": f"127.0.0.1:{_LOCAL_PROVIDERS['ollama']}",
    }


def test_ui_task_ids_match_synthetic_benchmark_catalog() -> None:
    metadata = load_ui_metadata()

    assert tuple(task["taskId"] for task in metadata["tasks"]) == tuple(
        task.task_id for task in SYNTHETIC_BENCHMARK_TASKS
    )


def test_ui_example_command_remains_unconfirmed_and_fixed() -> None:
    metadata = load_ui_metadata()
    safe_command = metadata["safeCommand"]

    assert safe_command == (
        "PYTHONPATH=apps/agent-api/src:packages/agent-core/src:packages/tools/src \\\n"
        "  uv run python -m sagent_agent_api.benchmark_cli"
    )
    assert "--confirmed" not in safe_command


def test_benchmark_component_remains_read_only_and_prompt_free() -> None:
    metadata = load_ui_metadata()
    component = COMPONENT_PATH.read_text(encoding="utf-8")
    button = re.search(
        r"<button(?P<attributes>[^>]*)>[\s\S]*?Benchmark starten[\s\S]*?</button>",
        component,
    )

    assert button is not None
    assert re.search(r"\bdisabled\b", button.group("attributes"))
    assert not re.search(r"\bon(?:Click|Submit)\s*=", button.group("attributes"))
    assert not re.search(
        r"<(?:input|textarea|select)\b|contentEditable|\bonChange\s*=",
        component,
    )

    forbidden_metadata_keys = {"prompt", "response", "modelText", "resultText"}

    def collect_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value).union(
                *(collect_keys(child) for child in value.values()),
            )
        if isinstance(value, list):
            return set().union(*(collect_keys(child) for child in value))
        return set()

    assert collect_keys(metadata).isdisjoint(forbidden_metadata_keys)
