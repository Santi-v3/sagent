# Tools

> **Pflegebereich:** geprüfte Basistools in `packages/tools`. Direkte MVP-4-Agent-Adapter liegen separat in `apps/agent-api`.

## Workspace und Dateien

`WorkspaceGuard` und `FileTool` erzwingen relative kanonische Pfade, sensible Pfadsperren, UTF-8-Grenzen und inhaltsgebundene Schreibnachweise.

## Tests

`TestRunner` verwendet feste serverseitige Profile, `shell=False`, bereinigte Umgebung, Timeout, Ressourcenlimits und redigierte Ausgabe.

## Git

`GitTool` liefert begrenzten Status und Diff und kann policy-konforme lokale Feature-Branches erstellen. Commit, Push und Merge sind blockiert.

## Abgrenzung zum Agent Loop

Die direkten Handler `bash`, `write_file`, `edit_file` und `grep` gehören nicht zu diesem Paket. Sie liegen in `apps/agent-api/src/sagent_agent_api/agent_loop.py` und besitzen andere, schwächere Sicherheitsgrenzen. Siehe [`docs/security/AGENT_LOOP.md`](../../docs/security/AGENT_LOOP.md).

## Tests

```bash
uv run pytest packages/tools/tests
uv run ruff check packages/tools
```
