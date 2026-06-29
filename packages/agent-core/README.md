# Agent Core

Deterministischer Sicherheitskern für Sagents Developer-Agent-Workflow.

MVP 1.C enthält:

- `WorkspaceGuard` für ausschließlich relative, kanonisch aufgelöste Pfade im gewählten Workspace
- Schutz vor Traversal, Symlink-Ausbrüchen und bekannten Secret-/Credential-Pfaden
- `FileTool` für begrenztes Lesen, Auflisten, Erstellen und Ändern von UTF-8-Textdateien
- `ChangeSetService` für alte/neue Inhalte, Unified Diffs und inhaltsgebundene Freigaben
- atomare Schreibvorgänge pro Datei erst nach einer exakten Approval-Prüfung

Löschen, freie Shell, Netzwerkzugriff, LLM-Aufrufe und automatische Git-Aktionen sind nicht Teil dieses Moduls.

## Tests

Vom Repository-Root:

```bash
uv run pytest packages/agent-core/tests
uv run ruff check packages/agent-core
```
