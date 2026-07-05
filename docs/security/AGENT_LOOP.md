# Agent-Loop-Sicherheit

> **Status:** experimentell, nicht produktionsreif. Quelle für Risiken und Härtungsanforderungen des MVP-4-Agent-Loops.

## Aktueller Ablauf

1. Das lokale Modell erhält Systemprompt, Conversation-, Memory- und Nutzerkontext.
2. Modelltext kann Blöcke im Format `TOOL_CALL: name` enthalten.
3. Der Parser extrahiert Name und JSON-Argumente.
4. Die Registry dispatcht den Handler unmittelbar.
5. Das Ergebnis wird als `TOOL_RESULT` in den nächsten Modellaufruf gegeben.
6. Nach höchstens zehn Iterationen oder drei Wiederholungen wird beendet.

## Werkzeugklassen

- direkt ausführend: `bash`, `grep`, Testausführung
- direkt schreibend: `write_file`, `edit_file`, `memory_store`
- ChangeSet-basiert: `code_edit_preview`, `code_edit_apply`
- Git: Status, Diff und lokale Branch-Erstellung
- lesend: Dateien, Glob, Listing und Memory-Suche

## Bekannte Lücken

- Arbeitsverzeichnis und PATH sind keine Betriebssystem-Sandbox.
- Shell-Kommandos können Fähigkeiten vorhandener Systemprogramme verwenden.
- direkte Pfadverkettung kann ohne vollständige Guard-Prüfung Workspace-Grenzen verletzen.
- internes Auto-Approval widerspricht der sichtbaren Human-in-the-loop-Grenze.
- untrusted Modelltext dient derzeit zugleich als Aktionsvorschlag und Dispatch-Auslöser.
- Tool-Ergebnisse können sensible Inhalte in weitere Modellrunden tragen.

## Zielzustand

- Modell erzeugt ausschließlich strukturierte, validierte Vorschläge.
- Eine deterministische Policy bewertet Capability, Pfad und Argumente.
- schreibende oder ausführende Aktionen erhalten externe, aktionsgebundene Approval-Tokens.
- alle Pfade werden kanonisch durch denselben `WorkspaceGuard` geprüft.
- Prozesse laufen über feste Profile oder eine echte OS-Sandbox.
- Ergebnisse werden begrenzt, redigiert und lokal auditiert.

## Mindesttests vor Freigabe

- absolute Pfade, `..`, Symlink-Ausbruch und Hidden-/Secret-Pfade
- Shell-Metazeichen, Subshells, Netzwerkprogramme und Umgebungszugriff
- Approval-Replay, Hash-Mismatch und veralteter Workspace
- übergroße Tool-Argumente und Ausgaben
- Prompt-Injection aus Workspace, Memory und Tool-Ergebnissen
- Wiederholung, Timeout und Abbruch laufender Prozesse
