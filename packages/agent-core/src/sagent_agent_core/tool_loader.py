"""Hot-plug tool loader – scan, load, install custom tools from ~/.sagent/tools/."""

import importlib.util
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

from sagent_agent_core.tool_registry import ToolDef, ToolRegistry


_TOOLS_DIR: Path | None = None


def _get_tools_dir() -> Path:
    global _TOOLS_DIR
    if _TOOLS_DIR is None:
        _TOOLS_DIR = Path(os.environ.get("SAGENT_TOOLS_DIR", Path.home() / ".sagent" / "tools"))
    _TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    (_TOOLS_DIR / "__init__.py").touch(exist_ok=True)
    return _TOOLS_DIR


def set_tools_dir(path: str | Path) -> None:
    global _TOOLS_DIR
    _TOOLS_DIR = Path(path)


def _tool_name_to_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
    return f"tool_{safe}.py"


def _filename_to_tool_name(filename: str) -> str | None:
    if filename.startswith("tool_") and filename.endswith(".py"):
        return filename[5:-3]
    return None


def scan_custom_tools() -> list[ToolDef]:
    """Scan the tools directory and return all loadable ToolDefs."""
    tools_dir = _get_tools_dir()
    results: list[ToolDef] = []
    for f in sorted(tools_dir.iterdir()):
        if not f.name.endswith(".py") or f.name == "__init__.py":
            continue
        name = _filename_to_tool_name(f.name)
        if not name:
            continue
        tool = load_custom_tool(name)
        if tool:
            results.append(tool)
    return results


def load_custom_tool(name: str) -> ToolDef | None:
    """Load a single custom tool by name from the tools directory."""
    tools_dir = _get_tools_dir()
    filepath = tools_dir / _tool_name_to_filename(name)
    if not filepath.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(name, filepath)
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        if hasattr(mod, "TOOL_DEF") and isinstance(mod.TOOL_DEF, ToolDef):
            return mod.TOOL_DEF
        return None
    except Exception:
        return None


def install_custom_tool(name: str, code: str) -> Path:
    """Write a custom tool .py file and return the path."""
    tools_dir = _get_tools_dir()
    filepath = tools_dir / _tool_name_to_filename(name)
    filepath.write_text(code, encoding="utf-8")
    return filepath


def uninstall_custom_tool(name: str) -> bool:
    """Delete a custom tool .py file. Returns True if deleted."""
    tools_dir = _get_tools_dir()
    filepath = tools_dir / _tool_name_to_filename(name)
    if filepath.exists():
        filepath.unlink()
        # Also remove from cache if loaded
        sys.modules.pop(name, None)
        return True
    return False


def list_custom_tools() -> list[dict[str, Any]]:
    """List installed custom tools with metadata."""
    tools_dir = _get_tools_dir()
    result: list[dict[str, Any]] = []
    for f in sorted(tools_dir.iterdir()):
        if not f.name.endswith(".py") or f.name == "__init__.py":
            continue
        name = _filename_to_tool_name(f.name)
        if not name:
            continue
        tool = load_custom_tool(name)
        status = "loaded" if tool else "error"
        result.append({
            "name": name,
            "status": status,
            "file": f.name,
            "description": tool.description if tool else "",
        })
    return result


def inject_custom_tools(registry: ToolRegistry) -> None:
    """Scan and register all custom tools into a ToolRegistry."""
    for tool in scan_custom_tools():
        if not registry.get(tool.name):
            registry.register(tool)


# ── Tool Templates ──

TOOL_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "shell-wrapper",
        "name": "Shell-Wrapper",
        "category": "shell",
        "description": "Wrapper um ein CLI-Tool (docker, kubectl, npm, pip, etc.) mit Argumenten und Output-Parsing",
        "prompt_hint": "Welches CLI-Tool soll gewrappt werden? Welche Subkommandos/Argumente werden benötigt?",
    },
    {
        "id": "api-client",
        "name": "API-Client",
        "category": "api",
        "description": "REST-API-Client mit GET/POST/PUT/DELETE, JSON-Parsing und Fehlerbehandlung",
        "prompt_hint": "Welche API (Basis-URL)? Welche Endpunkte werden benötigt? Auth-Methode (API-Key, Bearer, Basic)?",
    },
    {
        "id": "database-query",
        "name": "Datenbank-Query",
        "category": "db",
        "description": "SQL-Datenbank-Tool (SQLite, PostgreSQL, MySQL) mit Query-Ausführung und Result-Formatierung",
        "prompt_hint": "Welcher DB-Typ? Verbindungs-String/Datei? Erlaubte Query-Typen (SELECT, INSERT)?",
    },
    {
        "id": "web-scraper",
        "name": "Web-Scraper",
        "category": "web",
        "description": "Webseite fetchen, HTML parsen, CSS-Selektoren auswerten, strukturierte Daten extrahieren",
        "prompt_hint": "Welche URL(s)? Welche Daten extrahieren (CSS-Selektoren)? Pagination?",
    },
    {
        "id": "file-processor",
        "name": "Datei-Prozessor",
        "category": "file",
        "description": "Dateien einlesen, transformieren (CSV, JSON, XML, YAML) und schreiben",
        "prompt_hint": "Welche Dateiformate? Welche Transformation? Einzeldatei oder Batch?",
    },
    {
        "id": "notification",
        "name": "Notification-Sender",
        "category": "communication",
        "description": "Nachrichten senden via Slack, Discord, Email oder Webhook",
        "prompt_hint": "Welcher Kanal? Webhook-URL/API-Key? Nachrichtenformat?",
    },
]


def get_tool_templates() -> list[dict[str, Any]]:
    return [dict(t) for t in TOOL_TEMPLATES]


def render_template(template_id: str, tool_name: str, description: str, extra: dict[str, str] | None = None) -> str:
    """Render a template into full tool code by filling in the placeholders."""
    template_map = {t["id"]: t for t in TOOL_TEMPLATES}
    tmpl = template_map.get(template_id)
    if not tmpl:
        return ""
    safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in tool_name)

    if template_id == "shell-wrapper":
        return _render_shell_template(safe_name, description, extra or {})
    if template_id == "api-client":
        return _render_api_template(safe_name, description, extra or {})
    if template_id == "database-query":
        return _render_db_template(safe_name, description, extra or {})
    if template_id == "web-scraper":
        return _render_scraper_template(safe_name, description, extra or {})
    if template_id == "file-processor":
        return _render_file_template(safe_name, description, extra or {})
    if template_id == "notification":
        return _render_notification_template(safe_name, description, extra or {})

    return _render_generic_template(safe_name, description)


def _render_shell_template(name: str, description: str, extra: dict[str, str]) -> str:
    cli_tool = extra.get("cli_tool", name)
    return _T_SHELL.replace("__NAME__", name).replace("__DESC__", description).replace("__CLI_TOOL__", cli_tool)


def _render_api_template(name: str, description: str, extra: dict[str, str]) -> str:
    base_url = extra.get("base_url", "https://api.example.com")
    return _T_API.replace("__NAME__", name).replace("__DESC__", description).replace("__BASE_URL__", base_url)


def _render_db_template(name: str, description: str, extra: dict[str, str]) -> str:
    db_type = extra.get("db_type", "sqlite")
    conn_str = extra.get("connection", ":memory:")
    return _T_DB.replace("__NAME__", name).replace("__DESC__", description).replace("__CONN_STR__", conn_str)


def _render_scraper_template(name: str, description: str, extra: dict[str, str]) -> str:
    return _T_SCRAPER.replace("__NAME__", name).replace("__DESC__", description)


def _render_file_template(name: str, description: str, extra: dict[str, str]) -> str:
    return _T_FILE.replace("__NAME__", name).replace("__DESC__", description)


def _render_notification_template(name: str, description: str, extra: dict[str, str]) -> str:
    channel = extra.get("channel", "webhook")
    return _T_NOTIFY.replace("__NAME__", name).replace("__DESC__", description).replace("__CHANNEL__", channel)


def _render_generic_template(name: str, description: str) -> str:
    return _T_GENERIC.replace("__NAME__", name).replace("__DESC__", description)


_T_SHELL = '''"""
__NAME__ - __DESC__
Template: Shell-Wrapper
"""
import json
import subprocess
from sagent_agent_core.tool_registry import ToolDef, ToolResult


def __NAME___handler(command: str = "", __timeout: int = 30) -> str:
    """Fuhre __CLI_TOOL__-Befehl aus. command ist der komplette Befehl (ohne '__CLI_TOOL__')."""
    try:
        full_cmd = ["__CLI_TOOL__"] + (command.split() if command else [])
        result = subprocess.run(
            full_cmd,
            capture_output=True, text=True, timeout=__timeout,
        )
        return json.dumps({
            "exit_code": result.returncode,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "success": result.returncode == 0,
        }, ensure_ascii=False)
    except FileNotFoundError:
        return ToolResult.fail("'__CLI_TOOL__' nicht gefunden. Installiere es zuerst.")
    except subprocess.TimeoutExpired:
        return ToolResult.fail(f"Befehl nach {__timeout}s abgebrochen.")
    except Exception as e:
        return ToolResult.fail(str(e))


TOOL_DEF = ToolDef(
    name="__NAME__",
    description="__DESC__",
    parameters={"type": "object", "properties": {
        "command": {"type": "string", "description": "__CLI_TOOL__-Befehl und Argumente"},
        "timeout": {"type": "integer", "description": "Timeout in Sekunden", "default": 30},
    }, "required": ["command"]},
    handler=__NAME___handler,
)
'''

_T_API = '''"""
__NAME__ - __DESC__
Template: API-Client
"""
import json
from sagent_agent_core.tool_registry import ToolDef, ToolResult

try:
    import httpx
except ImportError:
    httpx = None


def __NAME___handler(endpoint: str = "/", method: str = "GET", body: str = "", headers: str = "") -> str:
    """Rufe REST-API auf."""
    if httpx is None:
        return ToolResult.fail("httpx nicht installiert. Fuhre 'pip install httpx' aus.")
    try:
        url = "__BASE_URL__".rstrip("/") + "/" + endpoint.lstrip("/")
        req_headers = {"Content-Type": "application/json"}
        if headers:
            extra = json.loads(headers) if headers.strip() else {}
            req_headers.update(extra)
        data = json.loads(body) if body.strip() else None
        r = httpx.request(method, url, json=data, headers=req_headers, timeout=30.0)
        try:
            resp_data = r.json()
        except Exception:
            resp_data = {"text": r.text[:2000]}
        return json.dumps({
            "status": r.status_code,
            "data": resp_data,
            "success": r.is_success,
        }, ensure_ascii=False)
    except Exception as e:
        return ToolResult.fail(str(e))


TOOL_DEF = ToolDef(
    name="__NAME__",
    description="__DESC__",
    parameters={"type": "object", "properties": {
        "endpoint": {"type": "string", "description": "API-Endpunkt (relativ zur Base-URL)"},
        "method": {"type": "string", "description": "HTTP-Methode", "default": "GET"},
        "body": {"type": "string", "description": "JSON-Body (optional)"},
        "headers": {"type": "string", "description": "JSON-Objekt mit extra Headern (optional)"},
    }, "required": ["endpoint"]},
    handler=__NAME___handler,
)
'''

_T_DB = '''"""
__NAME__ - __DESC__
Template: Datenbank-Query
"""
import json
import sqlite3
from sagent_agent_core.tool_registry import ToolDef, ToolResult


def __NAME___handler(query: str, params: str = "") -> str:
    """Fuhre SQL-Query aus. params ist optionales JSON-Array fur Parameter."""
    try:
        conn = sqlite3.connect("__CONN_STR__")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        q_params = json.loads(params) if params.strip() else []
        cur.execute(query, q_params)
        if query.strip().upper().startswith("SELECT"):
            rows = [dict(row) for row in cur.fetchall()]
            result = json.dumps({"rows": rows, "count": len(rows)}, ensure_ascii=False, default=str)
        else:
            conn.commit()
            result = json.dumps({"affected": cur.rowcount}, ensure_ascii=False)
        conn.close()
        return result
    except Exception as e:
        return ToolResult.fail(str(e))


TOOL_DEF = ToolDef(
    name="__NAME__",
    description="__DESC__",
    parameters={"type": "object", "properties": {
        "query": {"type": "string", "description": "SQL-Query"},
        "params": {"type": "string", "description": "JSON-Array mit Query-Parametern (optional)"},
    }, "required": ["query"]},
    handler=__NAME___handler,
)
'''

_T_SCRAPER = '''"""
__NAME__ - __DESC__
Template: Web-Scraper
"""
import json
import re
from sagent_agent_core.tool_registry import ToolDef, ToolResult

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    httpx = None
    BeautifulSoup = None


def __NAME___handler(url: str, selector: str = "", extract: str = "text") -> str:
    """Fetche URL und extrahiere Daten via CSS-Selektor."""
    if httpx is None or BeautifulSoup is None:
        return ToolResult.fail("Installiere 'pip install httpx beautifulsoup4'")
    try:
        r = httpx.get(url, timeout=30.0, follow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        if selector:
            elements = soup.select(selector)
            if extract == "text":
                data = [el.get_text(strip=True) for el in elements]
            elif extract == "html":
                data = [str(el) for el in elements]
            elif extract == "href":
                data = [el.get("href", "") for el in elements]
            elif extract == "src":
                data = [el.get("src", "") for el in elements]
            else:
                data = [el.get_text(strip=True) for el in elements]
        else:
            data = soup.get_text(strip=True)[:3000]
        return json.dumps({"data": data, "count": len(data) if isinstance(data, list) else 1, "url": url}, ensure_ascii=False)
    except Exception as e:
        return ToolResult.fail(str(e))


TOOL_DEF = ToolDef(
    name="__NAME__",
    description="__DESC__",
    parameters={"type": "object", "properties": {
        "url": {"type": "string", "description": "URL der Webseite"},
        "selector": {"type": "string", "description": "CSS-Selektor (optional, ohne wird gesamter Text extrahiert)"},
        "extract": {"type": "string", "description": "Was extrahieren: text/html/href/src", "default": "text"},
    }, "required": ["url"]},
    handler=__NAME___handler,
)
'''

_T_FILE = '''"""
__NAME__ - __DESC__
Template: Datei-Prozessor
"""
import json
import csv
import io
from pathlib import Path
from sagent_agent_core.tool_registry import ToolDef, ToolResult


def __NAME___handler(path: str, operation: str = "read", format: str = "text", content: str = "") -> str:
    """Lese/schreibe/transformiere Dateien. Unterstutzt text, json, csv."""
    try:
        p = Path(path)
        if operation == "read":
            if not p.exists():
                return ToolResult.fail(f"Datei nicht gefunden: {path}")
            if format == "json":
                data = json.loads(p.read_text())
            elif format == "csv":
                with p.open(newline="") as f:
                    reader = csv.DictReader(f)
                    data = [row for row in reader]
            else:
                data = p.read_text()[:10000]
            return json.dumps({"data": data}, ensure_ascii=False, default=str)
        elif operation == "write":
            p.parent.mkdir(parents=True, exist_ok=True)
            if format == "json":
                parsed = json.loads(content) if content.strip() else {}
                p.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
            else:
                p.write_text(content)
            return json.dumps({"status": "written", "path": str(p)}, ensure_ascii=False)
        else:
            return ToolResult.fail(f"Unbekannte Operation: {operation}")
    except Exception as e:
        return ToolResult.fail(str(e))


TOOL_DEF = ToolDef(
    name="__NAME__",
    description="__DESC__",
    parameters={"type": "object", "properties": {
        "path": {"type": "string", "description": "Dateipfad"},
        "operation": {"type": "string", "description": "read oder write", "default": "read"},
        "format": {"type": "string", "description": "text, json oder csv", "default": "text"},
        "content": {"type": "string", "description": "Inhalt bei write-Operation"},
    }, "required": ["path"]},
    handler=__NAME___handler,
)
'''

_T_NOTIFY = '''"""
__NAME__ - __DESC__
Template: Notification-Sender
"""
import json
from sagent_agent_core.tool_registry import ToolDef, ToolResult

try:
    import httpx
except ImportError:
    httpx = None


def __NAME___handler(message: str, webhook_url: str = "", title: str = "") -> str:
    """Sende eine Benachrichtigung."""
    if httpx is None:
        return ToolResult.fail("httpx nicht installiert. Fuhre 'pip install httpx' aus.")
    try:
        payload = {"text": message}
        if title:
            payload["title"] = title
        r = httpx.post(webhook_url or "__CHANNEL__", json=payload, timeout=15.0)
        return json.dumps({"status": r.status_code, "sent": r.is_success}, ensure_ascii=False)
    except Exception as e:
        return ToolResult.fail(str(e))


TOOL_DEF = ToolDef(
    name="__NAME__",
    description="__DESC__",
    parameters={"type": "object", "properties": {
        "message": {"type": "string", "description": "Nachrichtentext"},
        "webhook_url": {"type": "string", "description": "Webhook-URL (optional)"},
        "title": {"type": "string", "description": "Betreff/Titel (optional)"},
    }, "required": ["message"]},
    handler=__NAME___handler,
)
'''

_T_GENERIC = '''"""
__NAME__ - __DESC__
"""
import json
from sagent_agent_core.tool_registry import ToolDef, ToolResult


def __NAME___handler(**kwargs) -> str:
    """Implementierung des __NAME__-Tools."""
    try:
        result = {"status": "not_implemented", "tool": "__NAME__"}
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return ToolResult.fail(str(e))


TOOL_DEF = ToolDef(
    name="__NAME__",
    description="__DESC__",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=__NAME___handler,
)
'''
