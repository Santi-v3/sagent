import json
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ToolHandler = Callable[..., str]


@dataclass
class ToolResult:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str = ""

    def to_json(self) -> str:
        return json.dumps({
            "success": self.success,
            **self.data,
            "error": self.error,
        }, ensure_ascii=False)

    @classmethod
    def ok(cls, **data: Any) -> "ToolResult":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> "ToolResult":
        return cls(success=False, error=error)


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    handler: ToolHandler | None = None
    param_model: type | None = None


def _validate_args(
    args: dict[str, Any],
    parameters: dict[str, Any],
) -> str | None:
    """Validate args against JSON Schema. Returns error string or None."""
    required = parameters.get("required", [])
    props = parameters.get("properties", {})

    for key in required:
        if key not in args:
            return f"Fehlendes Pflichtfeld: {key}"

    for key, value in args.items():
        prop = props.get(key)
        if prop is None:
            continue
        prop_type = prop.get("type")
        if prop_type is not None:
            if prop_type == "string" and not isinstance(value, str):
                return f"Feld '{key}' muss ein String sein"
            if prop_type == "integer" and not isinstance(value, int):
                return f"Feld '{key}' muss eine Integer sein"
            if prop_type == "number" and not isinstance(value, (int, float)):
                return f"Feld '{key}' muss eine Zahl sein"
            if prop_type == "boolean" and not isinstance(value, bool):
                return f"Feld '{key}' muss ein Boolean sein"
            if prop_type == "array" and not isinstance(value, list):
                return f"Feld '{key}' muss ein Array sein"
            if prop_type == "object" and not isinstance(value, dict):
                return f"Feld '{key}' muss ein Objekt sein"

    # Set defaults for missing optional fields
    for key, prop in props.items():
        if key not in args and "default" in prop:
            args[key] = prop["default"]

    return None


TOOL_CALL_RE = r"^TOOL_CALL:\s*(\w+)\s*\n(.*?)(?:\nTOOL_RESULT:|\Z)"


class ToolPermission(Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


PermissionLike = ToolPermission | str


def _resolve_perm(p: PermissionLike) -> ToolPermission:
    if isinstance(p, ToolPermission):
        return p
    try:
        return ToolPermission(p)
    except ValueError:
        return ToolPermission.ALLOW


class ToolPermissionManager:
    def __init__(self, default: ToolPermission = ToolPermission.ALLOW) -> None:
        self._default: ToolPermission = default
        self._overrides: dict[str, ToolPermission] = {}

    @property
    def default(self) -> ToolPermission:
        return self._default

    @default.setter
    def default(self, value: ToolPermission) -> None:
        self._default = value

    def set(self, tool_name: str, permission: ToolPermission) -> None:
        if permission == self._default:
            self._overrides.pop(tool_name, None)
        else:
            self._overrides[tool_name] = permission

    def get(self, tool_name: str) -> ToolPermission:
        return self._overrides.get(tool_name, self._default)

    def reset(self, tool_name: str) -> None:
        self._overrides.pop(tool_name, None)

    def reset_all(self) -> None:
        self._overrides.clear()

    def to_dict(self) -> dict:
        return {
            "default": self._default.value,
            "overrides": {k: v.value for k, v in self._overrides.items()},
        }

    def from_dict(self, data: dict) -> None:
        self._default = _resolve_perm(data.get("default", "allow"))
        self._overrides = {
            k: _resolve_perm(v)
            for k, v in data.get("overrides", {}).items()
        }

    def check(self, tool_name: str) -> ToolPermission:
        return self.get(tool_name)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDef] = {}
        self._permissions: ToolPermissionManager = ToolPermissionManager()

    @property
    def permissions(self) -> ToolPermissionManager:
        return self._permissions

    def register(self, tool: ToolDef) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDef]:
        return list(self._tools.values())

    def to_openai_tools(self) -> list[dict]:
        tools: list[dict] = []
        for t in self._tools.values():
            if self._permissions.get(t.name) == ToolPermission.DENY:
                continue
            tool_def = {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            tools.append(tool_def)
        return tools

    def dispatch(self, name: str, args_json: str, check_permission: bool = True) -> str:
        tool = self.get(name)
        if tool is None:
            return ToolResult.fail(f"Unbekanntes Werkzeug: {name}").to_json()
        if tool.handler is None:
            return ToolResult.fail(f"Werkzeug {name} hat keinen Handler").to_json()

        if check_permission:
            perm = self._permissions.get(name)
            if perm == ToolPermission.DENY:
                return ToolResult.fail(
                    f"Werkzeug '{name}' ist gesperrt (Berechtigung: {perm.value})"
                ).to_json()
            if perm == ToolPermission.ASK:
                return json.dumps({
                    "success": False,
                    "requires_approval": True,
                    "tool": name,
                    "args": args_json,
                    "message": f"Zustimmung erforderlich für Werkzeug '{name}'",
                }, ensure_ascii=False)

        try:
            args = json.loads(args_json) if args_json.strip() else {}
        except json.JSONDecodeError as e:
            return ToolResult.fail(f"Ungültige JSON-Argumente für {name}: {e}").to_json()

        # Validate against JSON Schema
        validation_error = _validate_args(args, tool.parameters)
        if validation_error:
            return ToolResult.fail(validation_error).to_json()

        # Pydantic model validation (if param_model provided)
        if tool.param_model is not None:
            try:
                validated = tool.param_model(**args)
                args = validated.model_dump() if hasattr(validated, "model_dump") else vars(validated)
            except Exception as e:
                return ToolResult.fail(f"Validierungsfehler für {name}: {e}").to_json()

        try:
            result = tool.handler(**args)
            if isinstance(result, ToolResult):
                return result.to_json()
            if isinstance(result, dict):
                return json.dumps({"success": True, **result}, ensure_ascii=False)
            return result
        except TypeError as e:
            return ToolResult.fail(f"Falsche Argumente für {name}: {e}").to_json()
        except Exception as e:
            return ToolResult.fail(f"Fehler bei {name}: {e}").to_json()

    def system_prompt_block(self) -> str:
        parts = [
            "Du bist Sagent, ein lokaler KI-Assistent mit Zugriff auf Shell,"
            " Dateisystem, Git und Gedächtnis.",
            "",
            "## ZWINGENDE REGEL",
            "Der Benutzer erwartet echte Aktionen, nicht nur Worte."
            " Du MUSST ein TOOL_CALL ausführen BEVOR du antwortest.",
            "",
            "Beispiel 1:",
            'Benutzer: "Erstelle einen Ordner ~/Desktop/test"',
            "Deine Antwort (KEIN Text, sondern):",
            "TOOL_CALL: bash",
            '{"command": "mkdir ~/Desktop/test"}',
            "",
            "Beispiel 2:",
            'Benutzer: "Benenne ~/Desktop/test um in ~/Desktop/neu"',
            "Deine Antwort (KEIN Text, sondern):",
            "TOOL_CALL: bash",
            '{"command": "mv ~/Desktop/test ~/Desktop/neu"}',
            "",
            "Beispiel 3:",
            'Benutzer: "Wie heißt der Ordner?"',
            "Hier kannst du ohne TOOL_CALL antworten (reine Textfrage).",
            "",
            "MERKE: Bei JEDER Bitte um eine Aktion (erstellen, ändern, löschen,"
            " umbenennen, lesen, suchen) musst du ZUERST ein TOOL_CALL machen.",
            "- Antworte immer vollständig, logisch und mit vollem Kontext"
            " der Konversation.",
            "- Wenn dir Informationen fehlen, nutze ein Werkzeug um sie"
            " zu beschaffen.",
            "- Wähle den effizientesten Weg: ein einzelner bash-Befehl ist"
            " besser als drei.",
            "- Erkläre knapp, was du gemacht hast und warum.",
            "- Beziehe dich auf vorherige Schritte in der Konversation.",
            "- Bei Fehlern: sag genau, was schief ging und wie du es behebst.",
            "",
            "## Werkzeug-Aufruf (genaues Format einhalten!)",
            'TOOL_CALL: werkzeugname',
            '{"arg1": "wert1", "arg2": "wert2"}',
            "",
            "WICHTIG: Nach dem JSON kommen keine weiteren Zeichen, kein Text,"
            " keine Erklärung. Nur das JSON.",
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
