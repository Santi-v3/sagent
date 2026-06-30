"""Opt-in CLI for the fixed local-model benchmark suite."""

import argparse
import json
from collections.abc import Callable, Sequence

from sagent_agent_api.model_integration import build_model_router
from sagent_agent_core import (
    SYNTHETIC_BENCHMARK_TASKS,
    BenchmarkConfigurationError,
    BenchmarkConfirmationRequiredError,
    BenchmarkError,
    BenchmarkReport,
    LocalModelBenchmarkHarness,
    ModelContractError,
    ModelRouter,
    ModelTransport,
)

RouterBuilder = Callable[[], ModelRouter]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run Sagent's fixed synthetic benchmark against one explicitly configured "
            "IPv4 loopback model adapter."
        )
    )
    parser.add_argument(
        "--confirmed",
        action="store_true",
        help="Confirm the local model calls for this single benchmark run.",
    )
    return parser


def _report_payload(report: BenchmarkReport) -> dict[str, object]:
    return {
        "benchmark_id": report.benchmark_id,
        "adapter_id": report.adapter_id,
        "status": "completed",
        "observations": [
            {
                "task_id": observation.task_id,
                "status": observation.status.value,
                "reachable": observation.reachable,
                "latency_ms": observation.latency_ms,
                "response_duration_ms": observation.response_duration_ms,
                "total_duration_ms": observation.total_duration_ms,
                "response_characters": observation.response_characters,
                "response_untrusted": observation.response_untrusted,
                "cancellation_requested": observation.cancellation_requested,
                "cancellation_effective": observation.cancellation_effective,
                "error_code": observation.error_code,
                "prompt_stored": observation.prompt_stored,
            }
            for observation in report.observations
        ],
    }


def _print_json(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main(
    argv: Sequence[str] | None = None,
    *,
    router_builder: RouterBuilder = build_model_router,
) -> int:
    """Return a process code without ever printing prompts or provider error details."""

    args = _parser().parse_args(argv)
    if not args.confirmed:
        _print_json(
            {
                "benchmark_id": LocalModelBenchmarkHarness.BENCHMARK_ID,
                "error_code": "confirmation_required",
                "status": "blocked",
                "task_ids": [task.task_id for task in SYNTHETIC_BENCHMARK_TASKS],
            }
        )
        return 2

    try:
        router = router_builder()
        local_adapters = [
            descriptor
            for descriptor in router.list_adapters()
            if descriptor.transport is ModelTransport.LOOPBACK_HTTP
            and not descriptor.simulated
        ]
        if len(local_adapters) != 1:
            raise BenchmarkConfigurationError(
                "Exactly one configured loopback adapter is required."
            )
        harness = LocalModelBenchmarkHarness(router, local_adapters[0].adapter_id)
        report = harness.run(confirmed=True)
    except (BenchmarkConfigurationError, ModelContractError):
        _print_json(
            {
                "benchmark_id": LocalModelBenchmarkHarness.BENCHMARK_ID,
                "error_code": "local_configuration_invalid",
                "status": "blocked",
            }
        )
        return 2
    except BenchmarkConfirmationRequiredError:
        _print_json(
            {
                "benchmark_id": LocalModelBenchmarkHarness.BENCHMARK_ID,
                "error_code": "confirmation_required",
                "status": "blocked",
            }
        )
        return 2
    except BenchmarkError:
        _print_json(
            {
                "benchmark_id": LocalModelBenchmarkHarness.BENCHMARK_ID,
                "error_code": "benchmark_failed_safely",
                "status": "failed",
            }
        )
        return 1
    except Exception:
        _print_json(
            {
                "benchmark_id": LocalModelBenchmarkHarness.BENCHMARK_ID,
                "error_code": "benchmark_failed_safely",
                "status": "failed",
            }
        )
        return 1

    _print_json(_report_payload(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
