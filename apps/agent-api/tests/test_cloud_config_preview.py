"""Offline API tests for disabled cloud configuration metadata."""

from inspect import getsource
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sagent_agent_api.main import app, get_cloud_config_preview

client = TestClient(app)


def test_config_preview_returns_disabled_defaults() -> None:
    response = client.get("/cloud/config-preview")
    assert response.status_code == 200
    assert response.json() == {
        "provider_id": "deepseek-cloud",
        "enabled": False,
        "status": "not_configured",
        "transport_kind": "remote_http",
        "remote_http_allowed": False,
        "requires_explicit_approval": True,
        "approval_scope": "one_run_only",
        "secrets_source": "not_configured",
        "secrets_loaded": False,
        "endpoint_configured": False,
        "execution_allowed": False,
        "config_source": "static/offline/default",
        "cloud_execution": "No",
    }


def test_config_preview_does_not_read_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SAGENT_TEST_CLOUD_SECRET", "must-not-be-read")
    data = client.get("/cloud/config-preview").json()
    assert "must-not-be-read" not in repr(data)
    route_source = getsource(get_cloud_config_preview)
    assert "os.environ" not in route_source
    assert "os.getenv" not in route_source


def test_config_preview_contains_no_secret_or_address_fields() -> None:
    data = client.get("/cloud/config-preview").json()
    for field_name in (
        "api_key",
        "secret",
        "token",
        "credential",
        "endpoint",
        "url",
        "host",
        "port",
        "base_url",
    ):
        assert field_name not in data
    assert data["secrets_loaded"] is False
    assert data["endpoint_configured"] is False


def test_config_preview_does_not_activate_remote_http_or_router() -> None:
    data = client.get("/cloud/config-preview").json()
    assert data["transport_kind"] == "remote_http"
    assert data["remote_http_allowed"] is False
    assert data["execution_allowed"] is False
    route_source = getsource(get_cloud_config_preview)
    for forbidden in (
        "get_model_router",
        "ModelRouter",
        "allowed_transports",
        "cloud_providers_enabled",
    ):
        assert forbidden not in route_source


def test_config_preview_builds_no_provider_adapter_or_client() -> None:
    route_source = getsource(get_cloud_config_preview)
    for forbidden in (
        "build_provider",
        "create_provider",
        "ModelAdapter",
        "httpx",
        "socket",
        "requests",
    ):
        assert forbidden not in route_source


def test_config_preview_source_has_no_endpoint_or_network_literals() -> None:
    route_source = getsource(get_cloud_config_preview)
    assert "://" not in route_source
    assert "Authorization" not in route_source
    assert "Bearer" not in route_source

    module_source = Path(
        "packages/agent-core/src/sagent_agent_core/cloud_config.py"
    ).read_text("utf-8")
    assert "import os" not in module_source
    assert "import httpx" not in module_source
    assert "import socket" not in module_source
