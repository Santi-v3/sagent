"""MCP (Model Context Protocol) client for external tool servers.

Connects to external MCP servers via stdio transport, discovers tools,
and registers them in Sagent's ToolRegistry.
"""

import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from sagent_agent_core.tool_registry import ToolDef, ToolRegistry


@asynccontextmanager
async def mcp_session(
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> AsyncIterator[ClientSession]:
    """Start an MCP server subprocess and return a connected ClientSession.

    Usage:
        async with mcp_session("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]) as session:
            tools = await session.list_tools()
    """
    server_params = StdioServerParameters(
        command=command,
        args=args or [],
        env={**os.environ, **(env or {})},
        cwd=cwd,
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def _mcp_tool_to_dict(mcp_tool: Any) -> dict:
    """Convert an MCP Tool object to a dict for use in ToolRegistry."""
    input_schema = mcp_tool.inputSchema if hasattr(mcp_tool, "inputSchema") else {}
    if callable(getattr(input_schema, "model_dump", None)):
        input_schema = input_schema.model_dump()
    elif callable(getattr(input_schema, "dict", None)):
        input_schema = input_schema.dict()

    return {
        "type": "object",
        "properties": input_schema.get("properties", {}),
        "required": input_schema.get("required", []),
    }


async def list_mcp_tools(session: ClientSession) -> list[dict]:
    """List all tools from an MCP session returns as tool dicts."""
    result = await session.list_tools()
    tools: list[dict] = []
    for tool in result.tools:
        tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": _mcp_tool_to_dict(tool),
        })
    return tools


async def call_mcp_tool(
    session: ClientSession,
    name: str,
    arguments: dict[str, Any] | None = None,
) -> dict:
    """Call an MCP tool and return the result."""
    result = await session.call_tool(name, arguments)
    content_parts = []
    is_error = getattr(result, "isError", False)
    for item in (result.content or []):
        if hasattr(item, "text"):
            content_parts.append(item.text)
        elif hasattr(item, "data"):
            content_parts.append(str(item.data))
    return {
        "success": not is_error,
        "content": "\n".join(content_parts),
        "is_error": is_error,
    }


async def register_mcp_tools(
    session: ClientSession,
    registry: ToolRegistry,
    prefix: str = "mcp_",
) -> list[str]:
    """Discover tools from an MCP session and register them in the ToolRegistry.

    Returns list of registered tool names.
    """
    import asyncio

    mcp_tools = await list_mcp_tools(session)
    registered: list[str] = []
    for t in mcp_tools:
        tool_name = f"{prefix}{t['name']}"

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        def make_sync_handler(mcp_tool_name: str) -> Any:
            async def async_handler(**kwargs: Any) -> str:
                try:
                    result = await call_mcp_tool(session, mcp_tool_name, kwargs)
                    return json.dumps(result, ensure_ascii=False)
                except Exception as e:
                    return json.dumps(
                        {"success": False, "error": str(e), "content": ""},
                        ensure_ascii=False,
                    )

            def sync_handler(**kwargs: Any) -> str:
                return loop.run_until_complete(async_handler(**kwargs))
            return sync_handler

        tool_def = ToolDef(
            name=tool_name,
            description=t["description"],
            parameters=t["input_schema"],
            handler=make_sync_handler(t["name"]),
        )
        registry.register(tool_def)
        registered.append(tool_name)
    return registered
