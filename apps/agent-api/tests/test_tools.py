"""Tests for tool-related API endpoints."""
from fastapi.testclient import TestClient

from sagent_agent_api.main import app

client = TestClient(app)


def test_tool_suggest_skeleton() -> None:
    response = client.post("/tools/suggest", json={
        "name": "test_tool", "description": "A test tool", "use_llm": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_tool"
    assert "ToolDef" in data["code"]
    assert "test_tool_handler" in data["code"]


def test_tool_suggest_with_template() -> None:
    """If no templates exist, falls back to skeleton."""
    response = client.post("/tools/suggest", json={
        "name": "docker_helper",
        "description": "Manage Docker",
        "template_id": "nonexistent",
        "use_llm": False,
    })
    assert response.status_code == 200
    assert response.json()["name"] == "docker_helper"


def test_tool_templates_list() -> None:
    response = client.get("/tools/templates")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tool_install_validation() -> None:
    response = client.post("/tools/install", json={"name": ""})
    assert response.status_code == 422


def test_tool_install_skeleton() -> None:
    response = client.post("/tools/install", json={
        "name": "test_install_tool",
        "description": "Temp test",
        "use_llm": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "installed"
    assert data["name"] == "test_install_tool"
    assert "ToolDef" in data["code"]


def test_tool_installed_list() -> None:
    response = client.get("/tools/installed")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    names = [i["name"] for i in items]
    assert "test_install_tool" in names


def test_tool_suggest_with_llm_fallback() -> None:
    """LLM mode falls back to skeleton when no model is available."""
    response = client.post("/tools/suggest", json={
        "name": "llm_tool",
        "description": "LLM generated tool",
        "use_llm": True,
    })
    assert response.status_code == 200
    assert response.json()["name"] == "llm_tool"


def test_tool_uninstall() -> None:
    response = client.delete("/tools/installed/test_install_tool")
    assert response.status_code == 200

    response = client.get("/tools/installed")
    names = [i["name"] for i in response.json()]
    assert "test_install_tool" not in names
