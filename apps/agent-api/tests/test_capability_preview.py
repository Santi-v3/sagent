"""Tests for GET /capabilities/preview — offline capability policy metadata.

Every test verifies that the route returns safe metadata without any
runtime activation, secrets, endpoints, or side effects.
"""

from fastapi.testclient import TestClient

from sagent_agent_api.main import app

client = TestClient(app)


def test_capability_preview_returns_200() -> None:
    response = client.get("/capabilities/preview")
    assert response.status_code == 200


def test_capability_preview_contains_all_12_capabilities() -> None:
    response = client.get("/capabilities/preview")
    data = response.json()
    names = [c["name"] for c in data["capabilities"]]
    expected = [
        "read_workspace",
        "preview_file_edits",
        "apply_single_file_edit",
        "apply_multi_file_edit",
        "run_tests",
        "run_shell_command",
        "git_status",
        "git_commit",
        "git_push",
        "change_dependencies",
        "use_local_model",
        "use_cloud_model",
    ]
    assert names == expected


def test_capability_preview_policy_version_is_static() -> None:
    response = client.get("/capabilities/preview")
    assert response.json()["policy_version"] == "1.0.0"


def test_capability_preview_has_safety_flags_false() -> None:
    response = client.get("/capabilities/preview")
    data = response.json()
    assert data["shell_executed"] is False
    assert data["git_executed"] is False
    assert data["network_used"] is False
    assert data["cloud_used"] is False
    assert data["model_called"] is False
    assert data["runtime_activated"] is False


def test_capability_preview_use_cloud_model_is_disabled() -> None:
    response = client.get("/capabilities/preview")
    data = response.json()
    cloud = next(c for c in data["capabilities"] if c["name"] == "use_cloud_model")
    assert cloud["mode"] == "disabled"
    assert cloud["decision_for_execution"] == "denied"
    assert cloud["disabled"] is True


def test_capability_preview_use_local_model_needs_approval() -> None:
    response = client.get("/capabilities/preview")
    data = response.json()
    local = next(c for c in data["capabilities"] if c["name"] == "use_local_model")
    assert local["mode"] == "approval_required"
    assert local["requires_approval"] is True
    assert local["preview_only"] is False


def test_capability_preview_read_workspace_is_preview_only() -> None:
    response = client.get("/capabilities/preview")
    data = response.json()
    rw = next(c for c in data["capabilities"] if c["name"] == "read_workspace")
    assert rw["mode"] == "preview_only"
    assert rw["preview_only"] is True


def test_capability_preview_preview_file_edits_is_allowed() -> None:
    response = client.get("/capabilities/preview")
    data = response.json()
    pfe = next(c for c in data["capabilities"] if c["name"] == "preview_file_edits")
    assert pfe["mode"] == "allowed"
    assert pfe["disabled"] is False


def test_capability_preview_contains_no_secrets() -> None:
    response = client.get("/capabilities/preview")
    text = response.text
    assert "api_key" not in text
    assert "secret" not in text
    assert "token" not in text
    assert "password" not in text


def test_capability_preview_contains_no_endpoints_or_urls() -> None:
    response = client.get("/capabilities/preview")
    text = response.text
    assert "endpoint" not in text
    assert "host" not in text
    assert "port" not in text
    assert "url" not in text
    assert "http://" not in text
    assert "https://" not in text


def test_capability_preview_has_no_env_references() -> None:
    response = client.get("/capabilities/preview")
    text = response.text
    assert "getenv" not in text.lower()
    assert "environ" not in text.lower()
