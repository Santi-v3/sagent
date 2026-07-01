"""API tests for the offline cloud approval preview route.

Every test runs without network, without model calls, and without accessing
any API key, secret, or endpoint configuration.
"""

from fastapi.testclient import TestClient

from sagent_agent_api.main import app

client = TestClient(app)


def test_denied_by_default() -> None:
    response = client.post("/cloud/approval-preview", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["approval_status"] == "no_decision"
    assert data["is_valid"] is False
    assert data["is_approved"] is False
    assert data["explicit_confirmed"] is False
    assert data["provider_id"] == "deepseek-cloud"
    assert data["purpose"] == "coding"
    assert data["scope"] == "one_run_only"
    assert data["secrets_excluded"] is True
    assert data["full_repo_dump_blocked"] is True


def test_valid_one_run_only_approval() -> None:
    response = client.post(
        "/cloud/approval-preview",
        json={
            "approved": True,
            "explicit_confirmed": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["approval_status"] == "approved"
    assert data["is_valid"] is True
    assert data["is_approved"] is True
    assert data["explicit_confirmed"] is True


def test_denied_when_not_explicitly_confirmed() -> None:
    response = client.post(
        "/cloud/approval-preview",
        json={
            "approved": True,
            "explicit_confirmed": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["approval_status"] == "no_decision"
    assert data["is_valid"] is False
    assert data["is_approved"] is False
    assert data["explicit_confirmed"] is False


def test_custom_disclosure_fields() -> None:
    response = client.post(
        "/cloud/approval-preview",
        json={
            "disclosure": {
                "repo_context_included": True,
                "diffs_included": True,
                "files_included": True,
                "data_was_redacted": True,
                "bytes_estimate": 8192,
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["repo_context_included"] is True
    assert data["diffs_included"] is True
    assert data["files_included"] is True
    assert data["data_was_redacted"] is True
    assert data["bytes_estimate"] == 8192


def test_custom_provider_and_purpose() -> None:
    response = client.post(
        "/cloud/approval-preview",
        json={
            "provider_id": "deepseek-cloud",
            "purpose": "architecture",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "deepseek-cloud"
    assert data["purpose"] == "architecture"


def test_unknown_provider_rejected() -> None:
    response = client.post(
        "/cloud/approval-preview",
        json={"provider_id": "unknown-provider"},
    )
    assert response.status_code == 422


def test_local_provider_rejected() -> None:
    for pid in ("lm-studio", "ollama", "openai"):
        response = client.post(
            "/cloud/approval-preview",
            json={"provider_id": pid},
        )
        assert response.status_code == 422, f"Expected 422 for provider: {pid}"


def test_invalid_purpose_rejected() -> None:
    response = client.post(
        "/cloud/approval-preview",
        json={"purpose": "invalid-purpose"},
    )
    assert response.status_code == 422


def test_risk_hints_present() -> None:
    response = client.post("/cloud/approval-preview", json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data["risk_hints"]) >= 1
    assert any("external data transfer" in h for h in data["risk_hints"])


def test_response_has_no_endpoints_or_api_keys() -> None:
    response = client.post("/cloud/approval-preview", json={})
    assert response.status_code == 200
    data = response.json()
    assert "transport" not in data
    assert "endpoint" not in data
    assert "api_key" not in data
    assert "url" not in data
    assert "host" not in data
    assert "port" not in data
    assert "adapter" not in data
    assert "router" not in data
