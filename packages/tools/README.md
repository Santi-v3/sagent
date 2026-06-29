# Tools

Kleine, typisierte und policy-geprüfte Agent-Tools.

MVP 1.C implementiert `WorkspaceGuard` und `FileTool` für begrenzte UTF-8-Textdateien. Jeder Pfad wird kanonisch aufgelöst, bleibt relativ zum fixierten Workspace und wird gegen sensible Credential-Namen geprüft. Schreibmethoden akzeptieren ausschließlich eine intern signierte, inhaltsgebundene Freigabe des `ChangeSetService`.

MVP 1.D ergänzt den `TestRunner`. Er akzeptiert ausschließlich feste serverseitige Profile und gleicht vor jedem Start den angezeigten Befehl exakt ab. Prozesse laufen ohne `shell=True`, mit fixiertem Arbeitsverzeichnis, bereinigter Umgebung, Prozessgruppen-Timeout, CPU-/Dateideskriptorgrenzen und begrenzter, Secret-redigierter Ausgabe. Maximal 100 Ergebnisse bleiben im Prozessspeicher.

Allgemeiner Shell- oder unbeschränkter Dateisystemzugriff ist ausgeschlossen. Standard-Proxyvariablen werden auf einen lokalen Blackhole-Endpunkt gesetzt, ersetzen aber noch keine OS-Sandbox gegen absichtliche Raw-Socket- oder Dateisystemzugriffe aus Repository-Testcode. Bis zu dieser Sandbox dürfen nur bewusst geprüfte lokale Projekte ausgeführt werden. Löschen und das automatische Erstellen von Verzeichnissen werden weiterhin nicht unterstützt.

## Tests

Vom Repository-Root:

```bash
uv run pytest packages/tools/tests
uv run ruff check packages/tools
```
