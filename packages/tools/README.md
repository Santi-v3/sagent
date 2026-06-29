# Tools

Kleine, typisierte und policy-geprüfte Agent-Tools.

MVP 1.C implementiert `WorkspaceGuard` und `FileTool` für begrenzte UTF-8-Textdateien. Jeder Pfad wird kanonisch aufgelöst, bleibt relativ zum fixierten Workspace und wird gegen sensible Credential-Namen geprüft. Schreibmethoden akzeptieren ausschließlich eine intern signierte, inhaltsgebundene Freigabe des `ChangeSetService`.

Allgemeiner Shell-, Netzwerk- oder unbeschränkter Dateisystemzugriff ist ausgeschlossen. Löschen und das automatische Erstellen von Verzeichnissen werden bewusst noch nicht unterstützt.

## Tests

Vom Repository-Root:

```bash
uv run pytest packages/tools/tests
uv run ruff check packages/tools
```
