#!/usr/bin/env python3
"""MCP server that wraps Sagent's native tools (bash, write, edit, git, test).

Run directly as a stdio MCP server:
    python -m sagent_tools.mcp_server

Or connect from any MCP client via stdio.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "bash",
        "description": "Execute a shell command and return stdout/stderr/exit code.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                "workdir": {"type": "string", "description": "Working directory (default: cwd)", "default": "."},
            },
            "required": ["command"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file (creates or overwrites).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (relative to workspace)"},
                "content": {"type": "string", "description": "File content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace first occurrence of old_string with new_string in a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (relative to workspace)"},
                "old_string": {"type": "string", "description": "Text to replace"},
                "new_string": {"type": "string", "description": "Replacement text"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file and return its contents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (relative to workspace)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "grep",
        "description": "Search file contents using a regex pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "include": {"type": "string", "description": "File glob pattern (e.g. *.py)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "glob",
        "description": "List files matching a glob pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "git_status",
        "description": "Show git status of the workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "git_diff",
        "description": "Show git diff (unstaged changes).",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "git_commit",
        "description": "Stage all changes and create a commit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "git_log",
        "description": "Show recent git log entries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_count": {"type": "integer", "description": "Max commits", "default": 10},
            },
        },
    },
    {
        "name": "run_tests",
        "description": "Run tests for a given profile or command.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Test command to run"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 120},
            },
            "required": ["command"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web using DuckDuckGo. Returns top results (titles, URLs, snippets).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (1-20)", "default": 8},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_fetch",
        "description": "Fetch and extract text content from a URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 15},
            },
            "required": ["url"],
        },
    },
]


WORKSPACE_ROOT: str | None = None


def _get_workspace() -> str:
    global WORKSPACE_ROOT
    if WORKSPACE_ROOT is None:
        WORKSPACE_ROOT = os.environ.get("SAGENT_WORKSPACE", os.getcwd())
    return WORKSPACE_ROOT


def _safe_path(path: str) -> str:
    root = Path(_get_workspace()).resolve()
    abs_path = (root / path).resolve()
    if not str(abs_path).startswith(str(root)):
        return json.dumps({"error": f"Path {path} is outside workspace"})
    return str(abs_path)


def _handle_bash(args: dict) -> str:
    command = args["command"]
    timeout = args.get("timeout", 30)
    workdir = args.get("workdir", _get_workspace())
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )
        return json.dumps({
            "exit_code": result.returncode,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {timeout}s", "exit_code": -1})
    except Exception as e:
        return json.dumps({"error": str(e), "exit_code": -1})


def _handle_write_file(args: dict) -> str:
    path = _safe_path(args["path"])
    if path.startswith("{"):
        return path
    content = args["content"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return json.dumps({"status": "written", "path": args["path"], "size": len(content)})


def _handle_edit_file(args: dict) -> str:
    path = _safe_path(args["path"])
    if path.startswith("{"):
        return path
    old = args["old_string"]
    new = args["new_string"]
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if old not in content:
        return json.dumps({"error": f"String not found in {args['path']}"})
    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return json.dumps({"status": "edited", "path": args["path"]})


def _handle_read_file(args: dict) -> str:
    path = _safe_path(args["path"])
    if path.startswith("{"):
        return path
    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    return json.dumps({"path": args["path"], "content": content}, ensure_ascii=False)


def _handle_grep(args: dict) -> str:
    pattern = args["pattern"]
    include = args.get("include", "")
    workspace = _get_workspace()
    import platform
    if platform.system() == "Windows":
        try:
            matches = []
            for p in Path(workspace).rglob("*"):
                if include and not p.name.endswith(include.replace("*", "")):
                    continue
                if not p.is_file():
                    continue
                try:
                    for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
                        if pattern.lower() in line.lower():
                            matches.append(f"{p}:{i}:{line.strip()[:200]}")
                            if len(matches) >= 200:
                                break
                except Exception:
                    pass
            return json.dumps({"pattern": pattern, "matches": matches}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})
    else:
        cmd = f"grep -rn '{pattern}' {workspace}"
        if include:
            cmd += f" --include='{include}'"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10, cwd=workspace)
            lines = result.stdout.split("\n")[:200]
            return json.dumps({"pattern": pattern, "matches": lines}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})


def _handle_glob(args: dict) -> str:
    pattern = args["pattern"]
    workspace = _get_workspace()
    matches = [str(p) for p in Path(workspace).rglob(pattern)][:200]
    return json.dumps({"pattern": pattern, "matches": matches}, ensure_ascii=False)


def _handle_git_status(args: dict) -> str:
    workspace = _get_workspace()
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10, cwd=workspace)
        branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, timeout=5, cwd=workspace).stdout.strip()
        return json.dumps({"branch": branch, "porcelain": result.stdout.strip()}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _handle_git_diff(args: dict) -> str:
    workspace = _get_workspace()
    try:
        result = subprocess.run(["git", "diff"], capture_output=True, text=True, timeout=10, cwd=workspace)
        return json.dumps({"diff": result.stdout[:20000]}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _handle_git_commit(args: dict) -> str:
    workspace = _get_workspace()
    message = args["message"]
    try:
        subprocess.run(["git", "add", "-A"], capture_output=True, text=True, timeout=10, cwd=workspace)
        result = subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, timeout=10, cwd=workspace)
        return json.dumps({"status": "committed", "output": result.stdout.strip()}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _handle_git_log(args: dict) -> str:
    workspace = _get_workspace()
    max_count = args.get("max_count", 10)
    try:
        result = subprocess.run(["git", "log", f"--max-count={max_count}", "--oneline"], capture_output=True, text=True, timeout=10, cwd=workspace)
        return json.dumps({"log": result.stdout.strip().split("\n")}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _handle_run_tests(args: dict) -> str:
    command = args["command"]
    timeout = args.get("timeout", 120)
    workspace = _get_workspace()
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout, cwd=workspace)
        return json.dumps({
            "exit_code": result.returncode,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:5000],
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Tests timed out after {timeout}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _handle_web_search(args: dict) -> str:
    query = args["query"]
    max_results = min(args.get("max_results", 8), 20)
    try:
        import httpx2 as _httpx
        resp = _httpx.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; Sagent/1.0)"},
            timeout=15,
        )
        if resp.status_code != 200:
            return json.dumps({"error": f"DuckDuckGo returned {resp.status_code}"})

        results = []
        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self._in_result = False
                self._in_title = False
                self._in_snippet = False
                self._current = {}
                self._depth = 0

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "a" and attrs_dict.get("class") == "result__a":
                    self._in_title = True
                    self._current["url"] = attrs_dict.get("href", "")
                    self._current["title"] = ""
                elif tag == "a" and attrs_dict.get("class") == "result__snippet":
                    self._in_snippet = True
                    self._current["snippet"] = ""

            def handle_data(self, data):
                if self._in_title:
                    self._current["title"] = self._current.get("title", "") + data
                elif self._in_snippet:
                    self._current["snippet"] = self._current.get("snippet", "") + data

            def handle_endtag(self, tag):
                if tag == "a" and self._in_title:
                    self._in_title = False
                    if self._current.get("url") or self._current.get("title"):
                        self.results.append(self._current)
                    self._current = {}
                elif tag == "a" and self._in_snippet:
                    self._in_snippet = False

        parser = DDGParser()
        parser.feed(resp.text)
        results = parser.results[:max_results]

        return json.dumps({
            "query": query,
            "results": [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")}
                for r in results
            ],
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Web search failed: {e}"})


def _handle_web_fetch(args: dict) -> str:
    url = args["url"]
    timeout = args.get("timeout", 15)
    try:
        import httpx2 as _httpx
        resp = _httpx.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Sagent/1.0)"},
            timeout=timeout,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            return json.dumps({"error": f"HTTP {resp.status_code}", "url": url})

        import re
        text = resp.text
        # Strip HTML tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = text[:15000]

        return json.dumps({
            "url": url,
            "content": text,
            "content_type": resp.headers.get("content-type", ""),
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Fetch failed: {e}"})


HANDLERS: dict[str, Any] = {
    "bash": _handle_bash,
    "write_file": _handle_write_file,
    "edit_file": _handle_edit_file,
    "read_file": _handle_read_file,
    "grep": _handle_grep,
    "glob": _handle_glob,
    "git_status": _handle_git_status,
    "git_diff": _handle_git_diff,
    "git_commit": _handle_git_commit,
    "git_log": _handle_git_log,
    "run_tests": _handle_run_tests,
    "web_search": _handle_web_search,
    "web_fetch": _handle_web_fetch,
}


def _read_message() -> dict | None:
    """Read a JSON-RPC message from stdin (MCP stdio transport)."""
    header = sys.stdin.buffer.readline()
    if not header:
        return None
    if not header.startswith(b"Content-Length: "):
        return None
    length = int(header[len(b"Content-Length: "):].strip())
    sys.stdin.buffer.readline()  # blank line
    body = sys.stdin.buffer.read(length)
    return json.loads(body)


def _send_message(msg: dict) -> None:
    body = json.dumps(msg, ensure_ascii=False)
    sys.stdout.buffer.write(f"Content-Length: {len(body.encode())}\r\n\r\n{body}".encode())
    sys.stdout.buffer.flush()


def main() -> None:
    """Run the MCP server in stdio mode."""
    while True:
        msg = _read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            _send_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "sagent-native-tools", "version": "0.1.0"},
                },
            })

        elif method == "tools/list":
            _send_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOL_DEFINITIONS},
            })

        elif method == "tools/call":
            tool_name = msg.get("params", {}).get("name", "")
            arguments = msg.get("params", {}).get("arguments", {})
            handler = HANDLERS.get(tool_name)
            if handler is None:
                _send_message({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                })
            else:
                try:
                    result = handler(arguments)
                    _send_message({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {"content": [{"type": "text", "text": result}]},
                    })
                except Exception as e:
                    _send_message({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32000, "message": str(e)},
                    })

        elif method == "notifications/initialized":
            pass

        else:
            if msg_id:
                _send_message({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                })


if __name__ == "__main__":
    main()
