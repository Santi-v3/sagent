"""Tests for routing feedback store."""
from pathlib import Path
from sagent_agent_api.routing_feedback import RoutingFeedbackStore, get_feedback_store


def test_store_singleton() -> None:
    s1 = get_feedback_store()
    s2 = get_feedback_store()
    assert s1 is s2


def test_record_and_suggest() -> None:
    store = RoutingFeedbackStore(path=Path("/tmp/test_routing_feedback.json"))
    store.record(
        task="Schreibe eine Python-Funktion für Fibonacci",
        task_type="code",
        complexity="low",
        adapter_id="ollama:gemma4",
        transport="loopback_http",
        success=True,
    )
    suggestion = store.suggest_adapter(
        task="Schreibe eine Python-Funktion für Fibonacci",
        task_type="code",
        complexity="low",
        available=["ollama:gemma4", "groq:llama4"],
    )
    assert suggestion == "ollama:gemma4"


def test_suggest_empty_store() -> None:
    store = RoutingFeedbackStore(path=Path("/tmp/test_routing_empty.json"))
    suggestion = store.suggest_adapter(
        task="Test task",
        task_type="code",
        complexity="low",
        available=["ollama:gemma4"],
    )
    assert suggestion is None


def test_keyword_overlap_scoring() -> None:
    store = RoutingFeedbackStore(path=Path("/tmp/test_routing_scoring.json"))
    store.record(
        task="Schreibe einen API-Endpoint mit FastAPI",
        task_type="code",
        complexity="medium",
        adapter_id="ollama:gemma4",
        transport="loopback_http",
        success=True,
    )
    store.record(
        task="Schreibe einen API-Endpoint mit FastAPI und Datenbank",
        task_type="code",
        complexity="medium",
        adapter_id="groq:llama4",
        transport="cloud_http",
        success=True,
    )
    suggestion = store.suggest_adapter(
        task="Schreibe FastAPI-Endpoint",
        task_type="code",
        complexity="medium",
        available=["ollama:gemma4", "groq:llama4"],
    )
    assert suggestion is not None


def test_suggest_min_threshold() -> None:
    store = RoutingFeedbackStore(path=Path("/tmp/test_routing_threshold.json"))
    store.record(
        task="Koche Spaghetti Carbonara",
        task_type="cooking",
        complexity="low",
        adapter_id="ollama:gemma4",
        transport="loopback_http",
        success=True,
    )
    suggestion = store.suggest_adapter(
        task="Backe einen Kuchen",
        task_type="cooking",
        complexity="low",
        available=["ollama:gemma4"],
    )
    assert suggestion is None  # keyword overlap < 2


def test_failed_entry_ignored() -> None:
    store = RoutingFeedbackStore(path=Path("/tmp/test_routing_failed.json"))
    store.record(
        task="Schreibe Python-Code",
        task_type="code",
        complexity="low",
        adapter_id="ollama:gemma4",
        transport="loopback_http",
        success=False,
    )
    suggestion = store.suggest_adapter(
        task="Schreibe Python-Code",
        task_type="code",
        complexity="low",
        available=["ollama:gemma4"],
    )
    assert suggestion is None
