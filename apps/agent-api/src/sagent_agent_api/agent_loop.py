import json
import os
import re
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sagent_agent_core import (
    ModelCapability,
    ModelInputPart,
    ModelInputSource,
    ModelRequest,
    ModelRouter,
)
from sagent_agent_core.capability_policy import (
    CapabilityName,
    evaluate_capability,
    policy_for_safety_level,
)
from sagent_agent_core.tool_registry import ToolDef, ToolRegistry


@dataclass
class AgentLoopStep:
    text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentLoopResult:
    final_response: str = ""
    steps: list[AgentLoopStep] = field(default_factory=list)
    total_model_calls: int = 0
    duration_ms: float = 0.0
    error: str = ""


TOOL_CALL_RE = re.compile(r"^TOOL_CALL:\s*(\w+)\s*$", re.MULTILINE)

TOOL_CAPABILITY_MAP: dict[str, CapabilityName] = {
    "bash": CapabilityName.RUN_SHELL_COMMAND,
    "write_file": CapabilityName.APPLY_SINGLE_FILE_EDIT,
    "edit_file": CapabilityName.APPLY_SINGLE_FILE_EDIT,
    "read_file": CapabilityName.READ_WORKSPACE,
    "git_status": CapabilityName.GIT_STATUS,
    "git_commit": CapabilityName.GIT_COMMIT,
    "git_push": CapabilityName.GIT_PUSH,
    "run_tests": CapabilityName.RUN_TESTS,
    "change_dependencies": CapabilityName.CHANGE_DEPENDENCIES,
}


def _check_tool_allowed(tool_name: str, safety_level: str) -> str | None:
    """Return error message if tool is denied by policy, else None."""
    cap = TOOL_CAPABILITY_MAP.get(tool_name)
    if cap is None:
        return None
    policy = policy_for_safety_level(safety_level)
    decision = evaluate_capability(policy, cap)
    if decision.value in ("denied", "preview_only"):
        return f"Tool '{tool_name}' ist bei dieser Sicherheitsstufe nicht erlaubt."
    return None


def _build_request(
    system_prompt: str,
    user_task: str,
    conversation: list[dict[str, str]] | None = None,
    tool_result: str | None = None,
    memory_context: str | None = None,
) -> ModelRequest:
    parts: list[ModelInputPart] = [
        ModelInputPart(source=ModelInputSource.POLICY, content=system_prompt),
    ]
    if memory_context:
        parts.append(ModelInputPart(source=ModelInputSource.MEMORY, content=memory_context))
    if conversation:
        for msg in conversation:
            source = (
                ModelInputSource.USER
                if msg.get("role") == "user"
                else ModelInputSource.ASSISTANT
            )
            parts.append(ModelInputPart(source=source, content=msg.get("content", "")))
    parts.append(ModelInputPart(source=ModelInputSource.USER, content=user_task))
    if tool_result:
        parts.append(ModelInputPart(source=ModelInputSource.TOOL_RESULT, content=tool_result))
    return ModelRequest(
        capability=ModelCapability.CHAT,
        parts=tuple(parts),
        max_output_tokens=2048,
    )


def _extract_json(text: str) -> str:
    """Extrahiere das erste JSON-Objekt aus einem Text (ignoriere Folge-Text)."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        if depth == 0:
            return text[start:i+1]
    return text[start:] if start >= 0 else text


def _parse_tool_calls(text: str) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = TOOL_CALL_RE.match(lines[i])
        if m:
            name = m.group(1)
            args_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("TOOL_CALL:"):
                args_lines.append(lines[i])
                i += 1
            args_str = "\n".join(args_lines).strip()
            args_str = _extract_json(args_str)
            calls.append((name, args_str))
        else:
            i += 1
    return calls


def _make_bash(workspace_root: str) -> Callable[..., str]:
    def bash(command: str, timeout: int = 30) -> str:
        import subprocess
        try:
            result = subprocess.run(  # noqa: S602
                command,
                shell=True,
                cwd=workspace_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": os.environ.get("HOME", "")},
            )
            return json.dumps({
                "exit_code": result.returncode,
                "stdout": result.stdout[:10000],
                "stderr": result.stderr[:5000],
            }, ensure_ascii=False)
        except subprocess.TimeoutExpired:
            return json.dumps({"error": f"Command timed out after {timeout}s"}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    return bash


def _make_write_file(workspace_root: str) -> Callable[..., str]:
    def write_file(path: str, content: str) -> str:
        full_path = os.path.join(workspace_root, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        tmp = full_path + ".tmp"
        with open(tmp, "w") as f:
            f.write(content)
        os.replace(tmp, full_path)
        return json.dumps({
            "path": path, "status": "written",
            "size_bytes": len(content.encode("utf-8")),
        }, ensure_ascii=False)
    return write_file


def _make_edit_file(workspace_root: str) -> Callable[..., str]:
    def edit_file(path: str, old_string: str, new_string: str) -> str:
        full_path = os.path.join(workspace_root, path)
        if not os.path.isfile(full_path):
            return json.dumps({"error": f"File not found: {path}"}, ensure_ascii=False)
        with open(full_path) as f:
            content = f.read()
        if old_string not in content:
            return json.dumps({"error": f"String not found in {path}"}, ensure_ascii=False)
        count = content.count(old_string)
        new_content = content.replace(old_string, new_string)
        with open(full_path, "w") as f:
            f.write(new_content)
        return json.dumps({
            "path": path, "status": "edited", "occurrences": count,
        }, ensure_ascii=False)
    return edit_file


def _make_read_file(file_tool: Any, workspace_root: str) -> Callable[..., str]:
    def read_file(path: str) -> str:
        content = file_tool.read_file(path)
        data = {"path": path, "content": content, "size_bytes": len(content.encode("utf-8"))}
        return json.dumps(data, ensure_ascii=False)
    return read_file


def _make_glob(workspace_root: str) -> Callable[..., str]:
    def glob_search(pattern: str) -> str:
        matches = [str(p) for p in Path(workspace_root).rglob(pattern)]
        return json.dumps({"pattern": pattern, "matches": matches[:200]}, ensure_ascii=False)
    return glob_search


def _make_grep(workspace_root: str) -> Callable[..., str]:
    def grep(pattern: str, include: str = "") -> str:
        cmd = f"rg -n '{pattern}'"
        if include:
            cmd += f" -g '{include}'"
        cmd += f" {workspace_root}"
        import subprocess
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)  # noqa: S602
        lines = result.stdout.splitlines()[:200]
        return json.dumps({"pattern": pattern, "matches": lines}, ensure_ascii=False)
    return grep


def _make_list_files(file_tool: Any, workspace_root: str) -> Callable[..., str]:
    def list_files(path: str = ".") -> str:
        entries = file_tool.list_files(path)
        return json.dumps({"path": path, "entries": entries[:200]}, ensure_ascii=False)
    return list_files


def _make_git_status(git_tool: Any) -> Callable[..., str]:
    def git_status() -> str:
        s = git_tool.status()
        return json.dumps({
            "branch": s.branch, "clean": s.clean, "ahead": s.ahead,
            "behind": s.behind,
            "files": [
                f.to_dict() if hasattr(f, 'to_dict') else str(f)
                for f in s.files
            ],
        }, ensure_ascii=False, default=str)
    return git_status


def _make_git_diff(git_tool: Any) -> Callable[..., str]:
    def git_diff() -> str:
        d = git_tool.diff()
        return json.dumps({
            "staged": d.staged, "unstaged": d.unstaged, "untracked": d.untracked,
        }, ensure_ascii=False)
    return git_diff


def _make_git_create_branch(git_tool: Any) -> Callable[..., str]:
    def git_create_branch(name: str, expected_current_branch: str = "") -> str:
        s = git_tool.create_branch(name, expected_current_branch or None)
        return json.dumps({"branch": s.branch, "status": "created"}, ensure_ascii=False)
    return git_create_branch


def _make_code_edit_preview(code_edit: Any) -> Callable[..., str]:
    def code_edit_preview(path: str, new_content: str) -> str:
        cs = code_edit.preview(path, new_content)
        changes = []
        for fc in cs.changes:
            changes.append({
                "path": fc.path, "operation": fc.operation.value,
                "diff": fc.diff, "old_sha256": fc.old_sha256, "new_sha256": fc.new_sha256,
            })
        return json.dumps({
            "change_set_id": str(cs.change_set_id),
            "proposal_hash": cs.proposal_hash,
            "changes": changes,
        }, ensure_ascii=False)
    return code_edit_preview


def _make_code_edit_apply(code_edit: Any) -> Callable[..., str]:
    def code_edit_apply(change_set_id: str, proposal_hash: str) -> str:
        from uuid import UUID
        cs_id = UUID(change_set_id)
        # approve then apply
        code_edit.approve(cs_id, proposal_hash)
        code_edit.apply(cs_id, proposal_hash)
        return json.dumps({"status": "applied", "change_set_id": change_set_id}, ensure_ascii=False)
    return code_edit_apply


def _make_test_run_list(test_runner: Any) -> Callable[..., str]:
    def test_run_list() -> str:
        profiles = test_runner.list_profiles()
        return json.dumps([
            {"profile_id": p.profile_id, "display_name": getattr(p, 'display_name', p.profile_id),
             "timeout_seconds": getattr(p, 'timeout_seconds', 60)}
            for p in profiles
        ], ensure_ascii=False, default=str)
    return test_run_list


def _make_test_run_execute(test_runner: Any) -> Callable[..., str]:
    def test_run_execute(profile_id: str, expected_command: str = "") -> str:
        result = test_runner.run(profile_id, expected_command or None)
        return json.dumps({
            "result_id": str(result.result_id) if hasattr(result, 'result_id') else "",
            "passed": result.passed, "exit_code": result.exit_code,
            "stdout": result.stdout[:5000], "stderr": result.stderr[:2000],
            "duration_ms": result.duration_ms,
        }, ensure_ascii=False, default=str)
    return test_run_execute


def _make_memory_search(memory: Any) -> Callable[..., str]:
    def memory_search(query: str, n_results: int = 5) -> str:
        results = memory.search(query, n_results)
        return json.dumps([
            {"text": e.text, "score": round(s, 4), "category": e.metadata.get("category", "")}
            for e, s in results
        ], ensure_ascii=False)
    return memory_search


def _make_memory_store(memory: Any) -> Callable[..., str]:
    def memory_store(text: str, category: str = "") -> str:
        meta = {"category": category} if category else {}
        entry = memory.store(text, meta)
        return json.dumps({"id": entry.id, "status": "stored"}, ensure_ascii=False)
    return memory_store


def build_agent_registry(
    file_tool: Any,
    git_tool: Any,
    code_edit: Any,
    test_runner: Any,
    memory: Any,
    workspace_root: str,
) -> ToolRegistry:
    reg = ToolRegistry()

    reg.register(ToolDef(
        name="bash",
        description=(
            "Führe einen Shell-Befehl aus. "
            "Output ist auf 10000 Zeichen stdout, 5000 stderr begrenzt."
        ),
        parameters={
            "type": "object", "properties": {
                "command": {"type": "string", "description": "Der Shell-Befehl"},
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in Sekunden (max 60)",
                    "default": 30,
                },
            },
            "required": ["command"],
        },
        handler=_make_bash(workspace_root),
    ))
    reg.register(ToolDef(
        name="write_file",
        description=(
            "Schreibe Inhalt in eine Datei (überschreibt). "
            "Pfad ist relativ zum Workspace-Root."
        ),
        parameters={
            "type": "object", "properties": {
                "path": {"type": "string", "description": "Dateipfad relativ zum Workspace-Root"},
                "content": {"type": "string", "description": "Der vollständige neue Inhalt"},
            },
            "required": ["path", "content"],
        },
        handler=_make_write_file(workspace_root),
    ))
    reg.register(ToolDef(
        name="edit_file",
        description=(
            "Ersetze einen Text-String in einer Datei. "
            "Pfad ist relativ zum Workspace-Root."
        ),
        parameters={
            "type": "object", "properties": {
                "path": {"type": "string", "description": "Dateipfad relativ zum Workspace-Root"},
                "old_string": {"type": "string", "description": "Der zu ersetzende Text"},
                "new_string": {"type": "string", "description": "Der neue Text"},
            },
            "required": ["path", "old_string", "new_string"],
        },
        handler=_make_edit_file(workspace_root),
    ))
    reg.register(ToolDef(
        name="read_file",
        description=(
            "Lese den Inhalt einer Datei. "
            "Path ist relativ zum Workspace-Root."
        ),
        parameters={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        handler=_make_read_file(file_tool, workspace_root),
    ))
    reg.register(ToolDef(
        name="glob",
        description=(
            "Suche Dateien mit einem Glob-Pattern "
            "(z.B. **/*.py, src/**/*.tsx)."
        ),
        parameters={
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "required": ["pattern"],
        },
        handler=_make_glob(workspace_root),
    ))
    reg.register(ToolDef(
        name="list_files",
        description="Liste Dateien in einem Verzeichnis. Path ist relativ zum Workspace-Root.",
        parameters={"type": "object", "properties": {"path": {"type": "string", "default": "."}}},
        handler=_make_list_files(file_tool, workspace_root),
    ))
    reg.register(ToolDef(
        name="grep",
        description=(
            "Durchsuche Dateiinhalte mit einem Regex-Pattern. "
            "include ist optional (z.B. *.py)."
        ),
        parameters={
            "type": "object", "properties": {
                "pattern": {"type": "string", "description": "Regex-Pattern"},
                "include": {
                    "type": "string",
                    "description": "Datei-Glob-Filter (z.B. *.py, *.{ts,tsx})",
                },
            },
            "required": ["pattern"],
        },
        handler=_make_grep(workspace_root),
    ))
    reg.register(ToolDef(
        name="git_status",
        description="Zeige den aktuellen Git-Status: Branch, Änderungen, Ahead/Behind.",
        parameters={"type": "object", "properties": {}},
        handler=_make_git_status(git_tool),
    ))
    reg.register(ToolDef(
        name="git_diff",
        description="Zeige alle uncommitteten Änderungen als Diff.",
        parameters={"type": "object", "properties": {}},
        handler=_make_git_diff(git_tool),
    ))
    reg.register(ToolDef(
        name="git_create_branch",
        description="Erstelle einen neuen Feature-Branch.",
        parameters={
            "type": "object", "properties": {
                "name": {"type": "string", "description": "Branch-Name, z.B. feature/mein-feature"},
                "expected_current_branch": {
                    "type": "string",
                    "description": "Aktueller Branch (für Sicherheitscheck)",
                },
            },
            "required": ["name"],
        },
        handler=_make_git_create_branch(git_tool),
    ))
    reg.register(ToolDef(
        name="code_edit_preview",
        description="Zeige eine Vorschau für eine Code-Änderung an. Ändert noch nichts.",
        parameters={
            "type": "object", "properties": {
                "path": {"type": "string", "description": "Dateipfad relativ zum Workspace"},
                "new_content": {
                    "type": "string",
                    "description": "Der vollständige neue Inhalt der Datei",
                },
            },
            "required": ["path", "new_content"],
        },
        handler=_make_code_edit_preview(code_edit),
    ))
    reg.register(ToolDef(
        name="code_edit_apply",
        description="Wende eine zuvor mit code_edit_preview geprüfte Änderung an.",
        parameters={
            "type": "object", "properties": {
                "change_set_id": {
                    "type": "string",
                    "description": "Die change_set_id aus der Vorschau",
                },
                "proposal_hash": {
                    "type": "string",
                    "description": "Der proposal_hash aus der Vorschau",
                },
            },
            "required": ["change_set_id", "proposal_hash"],
        },
        handler=_make_code_edit_apply(code_edit),
    ))
    reg.register(ToolDef(
        name="test_run_list",
        description="Liste verfügbare Test-Profile auf.",
        parameters={"type": "object", "properties": {}},
        handler=_make_test_run_list(test_runner),
    ))
    reg.register(ToolDef(
        name="test_run_execute",
        description="Führe ein Test-Profil aus.",
        parameters={
            "type": "object", "properties": {
                "profile_id": {"type": "string", "description": "Profil-ID aus test_run_list"},
                "expected_command": {
                    "type": "string",
                    "description": "Erwarteter Befehl zur Bestätigung",
                },
            },
            "required": ["profile_id"],
        },
        handler=_make_test_run_execute(test_runner),
    ))
    reg.register(ToolDef(
        name="memory_search",
        description="Durchsuche das Gedächtnis nach relevanten Informationen.",
        parameters={
            "type": "object", "properties": {
                "query": {"type": "string", "description": "Suchbegriff"},
                "n_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
        handler=_make_memory_search(memory),
    ))
    reg.register(ToolDef(
        name="memory_store",
        description="Speichere eine Information im Gedächtnis.",
        parameters={
            "type": "object", "properties": {
                "text": {"type": "string", "description": "Der zu merkende Text"},
                "category": {
                    "type": "string",
                    "description": "Kategorie, z.B. tech, plan, decision",
                },
            },
            "required": ["text"],
        },
        handler=_make_memory_store(memory),
    ))
    return reg


def _get_memory_context(memory: Any, task: str, max_results: int = 5) -> str:
    """Suche relevante Memories und formatiere als Kontext-Block."""
    try:
        results = memory.search(task, max_results)
        if not results:
            return ""
        lines = ["Relevante Informationen aus dem Gedächtnis:"]
        for entry, score in results:
            cat = entry.metadata.get("category", "")
            tag = f"[{cat}]" if cat else ""
            lines.append(f"- {tag} (Ähnlichkeit: {score:.2f}) {entry.text[:300]}")
        return "\n".join(lines)
    except Exception:
        return ""


def _agent_loop_iteration(
    task: str,
    router: ModelRouter,
    registry: ToolRegistry,
    conversation: list[dict[str, str]] | None,
    memory: Any,
    kwargs: dict,
    tool_result_buffer: str | None,
    last_tool_name: str | None,
    repeat_count: int,
    system_prompt: str,
    iteration: int,
    safety_level: str = "balanced",
) -> tuple[str | None, str | None, list, str | None, int, str | None]:
    """Eine einzelne Agent-Loop-Iteration.

    Returns (error, final_response, calls, next_tool_result_buffer,
             next_repeat_count, next_last_tool_name).
    """
    memory_context = _get_memory_context(memory, task) if memory else ""
    req = _build_request(system_prompt, task, conversation, tool_result_buffer, memory_context)
    try:
        response = router.complete(req, **kwargs)
    except Exception as e:
        return f"Model call failed: {e}", None, [], None, repeat_count, last_tool_name

    text = response.content.strip()
    calls = _parse_tool_calls(text)

    # Repeat detection
    if last_tool_name and any(c[0] == last_tool_name for c in calls):
        repeat_count += 1
    else:
        repeat_count = 0
    if repeat_count >= 3:
        return (
            f"Agent loop aborted: repeated tool "
            f"'{last_tool_name}' 3 times",
            text, [], None, repeat_count, last_tool_name,
        )

    if not calls:
        return None, text, [], None, repeat_count, last_tool_name

    next_result = ""
    new_last = calls[0][0] if calls else last_tool_name
    for name, args_str in calls:
        denied = _check_tool_allowed(name, safety_level)
        if denied:
            tool_output = denied
        else:
            tool_output = registry.dispatch(name, args_str)
        next_result += f"TOOL_RESULT für {name}:\n{tool_output}\n\n"
    return None, None, [(name, args) for name, args in calls], next_result, repeat_count, new_last


def run_agent_loop(
    task: str,
    router: ModelRouter,
    registry: ToolRegistry,
    conversation: list[dict[str, str]] | None = None,
    max_iterations: int = 10,
    adapter_id: str | None = None,
    memory: Any = None,
    safety_level: str = "balanced",
) -> AgentLoopResult:
    result = AgentLoopResult()
    start = time.time()

    system_prompt = registry.system_prompt_block()
    tool_result_buffer: str | None = None
    iteration = 0
    kwargs = {}
    if adapter_id:
        kwargs["adapter_id"] = adapter_id
    last_tool_name: str | None = None
    repeat_count = 0

    while iteration < max_iterations:
        iteration += 1
        err, final_text, calls, next_buffer, repeat_count, last_tool_name = _agent_loop_iteration(
            task, router, registry, conversation, memory, kwargs,
            tool_result_buffer, last_tool_name, repeat_count, system_prompt, iteration,
            safety_level=safety_level,
        )
        step_text = final_text or (f"TOOL_CALL: {calls[0][0]}" if calls else "")
        step = AgentLoopStep(text=step_text)
        if calls:
            step.tool_calls = [{"name": name, "args": args} for name, args in calls]
        result.steps.append(step)
        result.total_model_calls += 1

        if err:
            result.error = err
            if final_text:
                result.final_response = final_text
            break
        if final_text:
            result.final_response = final_text
            break
        tool_result_buffer = next_buffer
    else:
        result.error = f"Max iterations ({max_iterations}) reached without final answer."

    result.duration_ms = (time.time() - start) * 1000
    if not result.final_response:
        result.final_response = result.steps[-1].text if result.steps else "Keine Antwort."
    return result


def run_agent_loop_stream(
    task: str,
    router: ModelRouter,
    registry: ToolRegistry,
    conversation: list[dict[str, str]] | None = None,
    max_iterations: int = 10,
    adapter_id: str | None = None,
    memory: Any = None,
    safety_level: str = "balanced",
) -> Generator[dict[str, Any], None, None]:
    """Generator-Version des Agent Loop für SSE-Streaming.
    
    Yields dicts mit Typen: model_text, tool_call, tool_result, done, error.
    """
    yield {"type": "status", "message": "Starte Agent-Loop..."}
    system_prompt = registry.system_prompt_block()
    tool_result_buffer: str | None = None
    iteration = 0
    kwargs = {}
    if adapter_id:
        kwargs["adapter_id"] = adapter_id
    last_tool_name: str | None = None
    repeat_count = 0
    start = time.time()
    total_calls = 0
    full_text = ""

    while iteration < max_iterations:
        iteration += 1
        yield {"type": "status", "message": f"Iteration {iteration}/{max_iterations}"}

        memory_context = _get_memory_context(memory, task) if memory else ""
        req = _build_request(system_prompt, task, conversation, tool_result_buffer, memory_context)
        try:
            response = router.complete(req, **kwargs)
        except Exception as e:
            yield {"type": "error", "message": f"Model call failed: {e}"}
            break

        total_calls += 1
        text = response.content.strip()
        calls = _parse_tool_calls(text)

        # Repeat detection
        if last_tool_name and any(c[0] == last_tool_name for c in calls):
            repeat_count += 1
        else:
            repeat_count = 0
        if repeat_count >= 3:
            yield {
                "type": "error",
                "message": (
                    f"Agent loop aborted: repeated tool "
                    f"'{last_tool_name}' 3 times (zuletzt: {text[:200]})"
                ),
            }
            break

        if not calls:
            yield {"type": "text", "content": text}
            full_text += text + "\n"
            break

        # Nur die Tool-Calls senden, nicht den rohen TOOL_CALL:-Text
        last_tool_name = calls[0][0]
        tool_result_buffer = ""
        for name, args_str in calls:
            yield {"type": "tool_call", "name": name, "args": args_str, "iteration": iteration}
            denied = _check_tool_allowed(name, safety_level)
            if denied:
                tool_output = denied
            else:
                tool_output = registry.dispatch(name, args_str)
            tool_result_buffer += f"TOOL_RESULT für {name}:\n{tool_output}\n\n"
            yield {
                "type": "tool_result", "name": name,
                "result": tool_output, "iteration": iteration,
            }
    else:
        yield {
            "type": "error",
            "message": f"Max iterations ({max_iterations}) reached without final answer.",
        }

    duration = (time.time() - start) * 1000
    yield {
        "type": "done", "full_text": full_text,
        "total_model_calls": total_calls,
        "duration_ms": round(duration, 1),
    }
