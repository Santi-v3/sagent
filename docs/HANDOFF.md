# Handoff

## Projektstatus

- **Phase:** MVP 1.B abgeschlossen
- **Stand:** 2026-06-29
- **Repository:** `Santi-v3/sagent`
- **Aktueller Fokus:** Vorbereitung von WorkspaceGuard, ChangeSet und sicheren Dateioperationen in MVP 1.C

## Fertiggestellt

- Monorepo-Verzeichnisse für Web, API, Agent-Core, Memory, Tools und Shared angelegt
- Root-Konfigurationen für pnpm, Turborepo und Python vorbereitet
- Produktvision, Architektur, Roadmap und konkrete Tasks dokumentiert
- Sicherheits-, Approval-, Memory- und Developer-Agent-Workflow festgelegt
- `docs/MASTER_PLAN.md` unverändert als kanonische Quelle für Vision und MVP-Reihenfolge übernommen
- FastAPI mit `GET /health` und deterministischem `POST /agent/task` implementiert
- pytest-Tests für Health, Task-Antwort und Whitespace-Validierung ergänzt
- Codex-nahe Next.js-Oberfläche mit Task-, Loading-, Success-, Offline- und Retry-Zuständen gebaut
- pnpm- und uv-Lockfiles erzeugt; Python auf 3.12 gepinnt
- Lint, TypeScript, pytest, Produktionsbuild und Browserflows erfolgreich geprüft
- Visueller Abgleich in `design-qa.md` mit `final result: passed` dokumentiert
- Deterministischen `TaskPlanner` mit Ziel, Schritten, Risiken und nächsten Aktionen implementiert
- `ChangeProposal` mit Risiko-Level, betroffenen Bereichen und benötigter Freigabe ergänzt
- In-Memory-Workflow mit `pending`, `approved`, `rejected` und `needs_changes` gebaut
- `POST /agent/plan`, `GET /agent/tasks/{id}` und `POST /agent/approve` ergänzt
- Codex-nahe Plan-, Risiko-, Proposal- und Approval-UI umgesetzt
- 10 API-Tests sowie Desktop-, Mobile- und Approval-Browserflows erfolgreich geprüft

## Bewusste Grenzen

- Workflow-Zustände sind noch nicht persistent und gehen beim API-Neustart verloren
- Keine LLM- oder Netzwerk-Integration
- Keine Dateiänderungs- oder Shell-Tools
- Tasks und Verlauf sind noch nicht persistent

## Nächster sinnvoller Schritt

MVP 1.C gemäß Abschnitt 25 des Masterplans umsetzen:

1. `WorkspaceGuard` für kanonische Pfade und sensible Dateien testgetrieben implementieren.
2. Datei-Tools ausschließlich hinter dem Guard definieren.
3. Änderungen als `ChangeSet` und Diff vorbereiten, noch ohne ungeprüfte Mutation.
4. Schreiben an eine inhaltsgebundene Freigabe koppeln.

Shell-Tools, externe Netzwerkzugriffe und echte Modellaufrufe bleiben ausdrücklich ausgeschlossen.

## Wichtige Leitplanken für die nächste Session

- Zuerst `docs/MASTER_PLAN.md`, danach `docs/SECURITY.md`, `docs/DECISIONS.md`, `docs/TASKS.md` und dieses Handoff lesen.
- Jede Aufgabe auf einem Feature-Branch abschließen: testen, committen, Branch pushen und PR gegen `main` erstellen.
- Niemals ohne ausdrückliche Nutzerbestätigung mergen oder Auto-Merge aktivieren.
- Keine schreibenden Tools vor einem getesteten Proposal-/Approval-Vertrag.
- Keine freie Shell und keine echten LLM-Aufrufe.
- Neue Architekturentscheidungen im Decision Log ergänzen.
- Tests für negative Sicherheitsfälle vor Happy-Path-Komfort priorisieren.

## Git-Abschluss jeder Aufgabe

Vor der Übergabe muss die nächste Session:

1. `git status`, Diff und Secret-/Privatdaten-Prüfung ausführen.
2. Alle relevanten Tests, Linter, Typprüfungen und Builds erfolgreich abschließen.
3. Einen klaren Conventional Commit auf dem Feature-Branch erstellen.
4. Den Feature-Branch ohne Force-Push zu GitHub pushen.
5. Einen PR gegen `main` erstellen oder Link und Anleitung liefern.
6. Branch, Commit, Push, PR, Tests, Dateien, Risiken und Worktree-Status berichten.

Der Nutzer prüft den PR. Kein Merge und kein Auto-Merge ohne seine ausdrückliche Bestätigung.

## Startprompt für eine Folgesession

> Lies docs/MASTER_PLAN.md vollständig und nutze ihn als strategische Quelle. Lies danach README.md, docs/SECURITY.md, docs/DECISIONS.md, docs/TASKS.md und docs/HANDOFF.md. Implementiere ausschließlich MVP 1.C: WorkspaceGuard, sichere Dateioperationen, ChangeSet und Diff mit Approval-Pflicht; weiterhin ohne LLMs, externe Netzwerkzugriffe oder freie Shell-Tools.
