"""Tests for MCP tool definitions and handlers in mcp_server.py."""
import json
from sagent_tools.mcp_server import TOOL_DEFINITIONS


def test_web_search_tool_defined() -> None:
    tool = next((t for t in TOOL_DEFINITIONS if t["name"] == "web_search"), None)
    assert tool is not None, "web_search tool not found in TOOL_DEFINITIONS"
    params = tool["inputSchema"]["properties"]
    assert "query" in params
    assert params["query"]["type"] == "string"


def test_web_fetch_tool_defined() -> None:
    tool = next((t for t in TOOL_DEFINITIONS if t["name"] == "web_fetch"), None)
    assert tool is not None, "web_fetch tool not found in TOOL_DEFINITIONS"
    params = tool["inputSchema"]["properties"]
    assert "url" in params
    assert params["url"]["type"] == "string"
    assert "timeout" in params


def test_tool_definitions_valid_json_schema() -> None:
    for tool in TOOL_DEFINITIONS:
        assert "name" in tool
        assert "inputSchema" in tool
        assert "type" in tool["inputSchema"]
        assert tool["inputSchema"]["type"] == "object"
        assert "properties" in tool["inputSchema"]


def test_tool_definitions_have_required_keys() -> None:
    required = {"name", "description", "inputSchema"}
    for tool in TOOL_DEFINITIONS:
        missing = required - set(tool.keys())
        assert not missing, f"Tool '{tool.get('name', '?')} missing keys: {missing}"


def test_web_search_timeout_configurable() -> None:
    tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "web_search")
    params = tool["inputSchema"]["properties"]
    assert "max_results" in params
    assert params["max_results"].get("default") == 8


def test_web_fetch_timeout_configurable() -> None:
    tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "web_fetch")
    params = tool["inputSchema"]["properties"]
    assert "timeout" in params
    assert params["timeout"].get("default") == 15
