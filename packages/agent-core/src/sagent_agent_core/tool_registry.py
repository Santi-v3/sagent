import json
from dataclasses import dataclass, field
from typing import Any, Callable


ToolHandler = Callable[..., str]


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    handler: ToolHandler | None = None


TOOL_CALL_RE = r"^TOOL_CALL:\s*(\w+)\s*\n(.*?)(?:\nTOOL_RESULT:|\Z)"


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDef]:
        return list(self._tools.values())

    def dispatch(self, name: str, args_json: str) -> str:
        tool = self.get(name)
        if tool is None:
            return json.dumps({"error": f"Unbekanntes Werkzeug: {name}"}, ensure_ascii=False)
        if tool.handler is None:
            return json.dumps({"error": f"Werkzeug {name} hat keinen Handler"}, ensure_ascii=False)
        try:
            args = json.loads(args_json) if args_json.strip() else {}
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Ungültige JSON-Argumente für {name}: {e}"}, ensure_ascii=False)
        try:
            result = tool.handler(**args)
            return result
        except TypeError as e:
            return json.dumps({"error": f"Falsche Argumente für {name}: {e}"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"Fehler bei {name}: {e}"}, ensure_ascii=False)

    def system_prompt_block(self) -> str:
        parts = [
            "Du hast Zugriff auf folgende Werkzeuge. Rufe sie auf, indem du exakt dieses Format verwendest:",
            "",
            'TOOL_CALL: werkzeugname',
            '{"arg1": "wert1", "arg2": "wert2"}',
            "",
            "Warte auf das TOOL_RESULT und setze dann die Aufgabe fort.",
            "Wenn du fertig bist, antworte normal ohne TOOL_CALL.",
            "",
            "--- Verfügbare Werkzeuge ---",
        ]
        for t in self._tools.values():
            parts.append(f"\n## {t.name}")
            parts.append(t.description)
            schema = json.dumps(t.parameters, ensure_ascii=False, indent=2)
            parts.append(f"Parameter: {schema}")
        parts.append("\n--- Ende der Werkzeugliste ---")
        return "\n".join(parts)
