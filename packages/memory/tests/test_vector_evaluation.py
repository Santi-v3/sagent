from dataclasses import FrozenInstanceError

import pytest
from sagent_memory import (
    InMemoryVectorStore,
    VectorEvaluationReport,
    evaluate_vector_store,
)


def test_synthetic_evaluation_passes_for_offline_in_memory_adapter() -> None:
    report = evaluate_vector_store("offline-in-memory", InMemoryVectorStore)

    assert report.passed is True
    assert all(report.checks.values())
    assert report.synthetic_only is True
    assert report.network_used is False
    assert report.model_called is False


def test_report_and_checks_are_immutable() -> None:
    report = evaluate_vector_store("offline-in-memory", InMemoryVectorStore)

    with pytest.raises(TypeError):
        report.checks["network_used"] = True  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        report.passed = False  # type: ignore[misc]


def test_adapter_identifier_is_bounded() -> None:
    with pytest.raises(ValueError, match="adapter_id"):
        evaluate_vector_store("", InMemoryVectorStore)


def test_evaluation_report_contains_no_provider_configuration() -> None:
    fields = VectorEvaluationReport.__dataclass_fields__

    assert "url" not in fields
    assert "endpoint" not in fields
    assert "api_key" not in fields
    assert "model" not in fields
