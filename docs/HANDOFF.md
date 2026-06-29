# Handoff

## Projektstatus

- **Phase:** MVP 1.D abgeschlossen
- **Stand:** 2026-06-29
- **Repository:** `Santi-v3/sagent`
- **Aktueller Fokus:** Vorbereitung des sicheren Git-Status-, Diff- und Branch-Workflows in MVP 1.E

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
- `WorkspaceGuard` mit fixiertem kanonischem Root und relativer Pfadpflicht implementiert
- Absolute Pfade, Traversal, Symlink-Ausbrüche, `.env`, SSH-Schlüssel sowie Token-/Secret-/Credential-Pfade blockiert
- `FileTool` für begrenztes Lesen, Auflisten, atomisches Erstellen und Ändern von UTF-8-Textdateien ergänzt
- Unveränderliche ChangeSets mit alten/neuen Inhalten, SHA-256-Werten und Unified Diffs implementiert
- Inhaltsgebundene Freigabe mit exaktem Proposal-Hash, intern signierten Schreibnachweisen und Stale-Workspace-Prüfung umgesetzt
- 22 neue Core-/Tool-Tests für Sicherheitsgrenzen, Konflikte und erlaubte Dateiänderungen erfolgreich geprüft
- Allowlist-basierten `TestRunner` ohne freie Request-Kommandos und ohne `shell=True` implementiert
- Feste Profile für Projekt-pytest, Python-ruff und lokales Web-ESLint ergänzt
- Task-Approval und exakten Anzeigebefehl als doppelte API-Gates vor Prozessstart eingebaut
- Timeout, Prozessgruppen-Abbruch, CPU-/Dateideskriptorgrenzen, bereinigte Umgebung und lokale Proxy-Sperre ergänzt
- stdout/stderr auf 64 KiB begrenzt, bekannte Secrets redigiert und Ergebnis-Historie auf 100 Einträge begrenzt
- `GET /agent/test-profiles`, `POST /agent/run-tests` und `GET /agent/test-results/{id}` implementiert
- UI um Profilwahl, sichtbaren Befehl, Loading-, Bestanden-, Fehlgeschlagen- und Log-Zustände erweitert
- 46 Python-Tests sowie echte Runner-Läufe für pytest, ruff und Web-ESLint erfolgreich geprüft
- Desktop- und Mobile-Browserfluss für erfolgreiche und fehlgeschlagene Tests ohne Konsolenfehler geprüft

## Bewusste Grenzen

- Workflow-Zustände sind noch nicht persistent und gehen beim API-Neustart verloren
- Keine LLM- oder Netzwerk-Integration
- Datei-Tools sind noch nicht an API oder UI angebunden; ChangeSet-Zustände bleiben im Prozessspeicher
- Mehrdatei-ChangeSets sind pro Datei atomar, aber noch keine globale Dateisystemtransaktion
- Testprozesse haben noch keine echte macOS-Dateisystem-/Netzwerk-Sandbox; nur bewusst geprüfte lokale Workspaces ausführen
- Tasks und Verlauf sind noch nicht persistent

## Nächster sinnvoller Schritt

MVP 1.E gemäß Abschnitt 27 des Masterplans umsetzen:

1. Git-Status, aktuellen Branch und Diff zunächst read-only und strukturiert bereitstellen.
2. Feature-Branch-Erstellung mit explizitem Schutz vor Arbeit auf `main` implementieren.
3. Commit-Vorbereitung an sichtbaren Diff und eine exakte Freigabe koppeln.
4. Push, Force-Push, Merge und Auto-Merge im Agent-Tool ohne gesonderte Freigabe blockieren.
5. API, UI und negative Tests für `main`-Schutz und verbotene Git-Aktionen ergänzen.

Shell-Tools, externe Netzwerkzugriffe und echte Modellaufrufe bleiben ausdrücklich ausgeschlossen.

## Wichtige Leitplanken für die nächste Session

- Zuerst `docs/MASTER_PLAN.md`, danach `docs/SECURITY.md`, `docs/DECISIONS.md`, `docs/TASKS.md` und dieses Handoff lesen.
- Jede Aufgabe auf einem Feature-Branch abschließen: testen, committen, Branch pushen und PR gegen `main` erstellen.
- Niemals ohne ausdrückliche Nutzerbestätigung mergen oder Auto-Merge aktivieren.
- Datei-Schreibzugriffe ausschließlich über den getesteten ChangeSet-/Approval-Vertrag führen.
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

> Lies docs/MASTER_PLAN.md vollständig und nutze ihn als strategische Quelle. Lies danach README.md, docs/SECURITY.md, docs/DECISIONS.md, docs/TASKS.md und docs/HANDOFF.md. Implementiere ausschließlich MVP 1.E: sicheren Git-Status, Diff und Feature-Branch-Unterstützung mit Approval-Pflicht; weiterhin ohne LLMs, unkontrollierte Pushes, Merge oder freie Shell-Kommandos.
