# Agent Core

Deterministischer Sicherheitskern für Sagents Developer-Agent-Workflow.

MVP 1.C enthält:

- `WorkspaceGuard` für ausschließlich relative, kanonisch aufgelöste Pfade im gewählten Workspace
- Schutz vor Traversal, Symlink-Ausbrüchen und bekannten Secret-/Credential-Pfaden
- `FileTool` für begrenztes Lesen, Auflisten, Erstellen und Ändern von UTF-8-Textdateien
- `ChangeSetService` für alte/neue Inhalte, Unified Diffs und inhaltsgebundene Freigaben
- atomare Schreibvorgänge pro Datei erst nach einer exakten Approval-Prüfung

MVP 2.A ergänzt:

- provider-neutrale, unveränderliche Request-, Response-, Usage- und Adapter-Verträge
- Provenienzlabels für Policy-, Nutzer-, Workspace-, Memory- und Tool-Ergebnis-Text
- explizite Fähigkeiten für Chat und Coding sowie getrennte Transportklassen
- einen deterministischen In-Process-Fake ohne Modell-, Netzwerk- oder Tool-Aufruf
- einen `ModelRouter` mit festen Routen, Input-/Output-Limits und standardmäßiger Sperre für Loopback- und Remote-HTTP
- Antworten, die technisch unveränderlich als `untrusted=true` markiert sind und keine Tool-Call-Struktur besitzen

Löschen, freie Shell, Netzwerkzugriff, echte LLM-Aufrufe und automatische Git-Aktionen sind nicht Teil dieses Moduls.

## Tests

Vom Repository-Root:

```bash
uv run pytest packages/agent-core/tests
uv run ruff check packages/agent-core
```
