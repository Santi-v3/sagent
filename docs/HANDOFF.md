# Handoff

## Projektstatus

- **Phase:** MVP 1 abgeschlossen; MVP 2.A abgeschlossen
- **Stand:** 2026-06-29
- **Repository:** `Santi-v3/sagent`
- **Aktueller Fokus:** MVP 2.B – abgesicherter Loopback-HTTP-Adapter für lokale OpenAI-kompatible Modellserver

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
- Repository-gebundenen `GitTool` mit festem Git-Executable, bereinigter Umgebung, Timeout sowie Output- und Statuslimits implementiert
- Strukturierten Branch-, Ahead-/Behind- und Worktree-Status mit sichtbarer Warnung auf `main`, `master`, `trunk` und Detached HEAD ergänzt
- Staged, unstaged und unversionierte Textänderungen als begrenzten Diff zusammengeführt; sensible Pfade verborgen und bekannte Secrets redigiert
- Lokale Feature-Branch-Erstellung auf `codex/`, `feature/`, `fix/`, `docs/`, `test/` und `chore/` begrenzt und an den angezeigten Ausgangsbranch gebunden
- Nicht ausführende Commit-Vorbereitung an Conventional-Commit-Message und exakten Diff-Hash gekoppelt; kein Staging und kein Commit
- Push und Merge im Tool vollständig blockiert; keine Push-/Merge-Routen oder -Buttons ergänzt
- `GET /git/status`, `GET /git/diff` und bestätigtes `POST /git/branch` implementiert
- UI um Branch-Badge, Statusübersicht, Dateiliste, `main`-Warnung, lokale Branch-Erstellung und scrollbaren Diff erweitert
- Git-Tool und API mit 14 fokussierten Tests geprüft; vollständige Projektprüfung siehe letzter Aufgabenabschluss im PR
- Kriterien für MVP 1 aus Abschnitt 28 des Masterplans gegen Implementierung, Tests und lokale Startfähigkeit auditiert
- Provider-neutrale Modellverträge für source-labelled Input, Capability, Request, Response, Usage und Adapter-Metadaten implementiert
- Transportklassen `in_process`, `loopback_http` und `remote_http` modelliert; Router-Allowlist erlaubt derzeit ausschließlich `in_process`
- Deterministischen `FakeModelAdapter` ohne Modell-, Netzwerk- oder Tool-Aufruf für Chat und Coding ergänzt
- `ModelRouter` mit festen Capability-Routen, Part-/Input-/Output-Limits, Streaming-Gate und Response-Identity-Prüfung implementiert
- Modellantworten unveränderlich als `untrusted=true` modelliert; der Adaptervertrag enthält keine Tool-Call- oder Policy-Schnittstelle
- `GET /models` und `POST /models/preview` für Discovery und begrenzte Offline-Simulation ergänzt
- 14 fokussierte Core-/API-Tests für Determinismus, Injection-Text, Limits, Routing, blockierte echte Adapter/Transporte und fehlerhafte Adapterantworten erfolgreich geprüft

## MVP-1-Abschlussaudit

- **Struktur und Start:** Monorepo ist getrennt in Web, API, Core, Tools, Memory und Shared; Web und API starten lokal über `pnpm dev`.
- **Health und Intake:** `GET /health` antwortet strukturiert; Aufgaben können in der Weboberfläche eingegeben und an die lokale API gesendet werden.
- **Plan und Proposal:** Der deterministische Planner erzeugt Ziel, Schritte, Risiken, nächste Aktionen und einen Änderungsvorschlag.
- **Human Approval:** Nutzer können Vorschläge freigeben, ablehnen oder Überarbeitung verlangen; ungültige Zustandswechsel werden serverseitig blockiert.
- **Workspace und Secrets:** `WorkspaceGuard`, sensible Pfadregeln, inhaltsgebundene ChangeSets und Redaction begrenzen Datei- und Logzugriffe.
- **Diff und Tests:** ChangeSet- und Git-Diffs sind sichtbar; ausschließlich allowlist-basierte Testprofile können nach Freigabe ausgeführt werden, Ergebnisse erscheinen strukturiert in der UI.
- **Git:** Branch und Status sind sichtbar, `main` erzeugt eine Warnung, Feature-Branch-Erstellung ist eingeschränkt und Push/Merge bleiben blockiert.
- **Gefährliche Aktionen:** Keine freie Shell, kein allgemeiner Netzwerkzugriff, kein automatischer Commit, kein Push und kein Merge im Sagent-Tool.
- **Dokumentation:** README, Architektur, Roadmap, Tasks, Decisions, Security, Workflow und dieses Handoff bilden den Stand von MVP 1 ab.

## Bewusste Grenzen

- Workflow-Zustände sind noch nicht persistent und gehen beim API-Neustart verloren
- Keine echte LLM- oder Netzwerk-Integration; die Modellvorschau ist ein In-Process-Fake
- Datei-Tools sind noch nicht an API oder UI angebunden; ChangeSet-Zustände bleiben im Prozessspeicher
- Mehrdatei-ChangeSets sind pro Datei atomar, aber noch keine globale Dateisystemtransaktion
- Testprozesse haben noch keine echte macOS-Dateisystem-/Netzwerk-Sandbox; nur bewusst geprüfte lokale Workspaces ausführen
- Tasks und Verlauf sind noch nicht persistent
- Git-Status und Diff sind an dieses Repository gebunden; eine sichere Workspace-Auswahl ist noch nicht implementiert
- Die Commit-Vorbereitung ist nur ein unveränderlicher Plan. Sagent kann selbst weder stagen noch committen, pushen oder mergen
- Secret-Erkennung ist absichtlich konservativ und musterorientiert; ein Treffer blockiert die Commit-Vorbereitung, ersetzt aber keinen manuellen Secret-Scan
- Die visuelle Git-Ansicht wurde im laufenden Feature-Branch geprüft; der isolierte `main`-Browserdurchlauf wurde durch wiederholte Unterbrechungen der lokalen Browserverbindung nicht vollständig automatisiert. API- und Tool-Tests decken `main`-Warnung und Branch-Wechsel ab
- `loopback_http` und `remote_http` sind nur Typen im Vertrag und werden vom aktuellen Router blockiert
- Es gibt noch kein Streaming, keine Modellserver-Erkennung, keine sichere Endpoint-Konfiguration und keinen echten Modellvergleich

## Nächster sinnvoller Schritt

MVP 2.B als separates Sicherheitsinkrement umsetzen:

1. Endpoint-Konfiguration ausschließlich für kanonische `http://127.0.0.1`-/`http://[::1]`-URLs und erlaubte Ports definieren.
2. Redirects, DNS-Namen, Unix-Sockets, Proxyvererbung und Credential-Übernahme blockieren.
3. OpenAI-kompatiblen Request/Response-Transport mit Timeout, Abbruch und harten Größenlimits implementieren.
4. Nicht erreichbaren Server, Timeout, Redirect, ungültiges JSON, falsche IDs und übergroße Antworten negativ testen.
5. LM Studio und Ollama lokal anhand derselben reproduzierbaren Coding-Aufgaben evaluieren; erst danach UI-Integration erwägen.

Kostenpflichtige APIs, externe Modellendpunkte, freie Shell und Modell-gesteuerte Policy-Entscheidungen bleiben ausdrücklich ausgeschlossen.

## Wichtige Leitplanken für die nächste Session

- Zuerst `docs/MASTER_PLAN.md`, danach `docs/SECURITY.md`, `docs/DECISIONS.md`, `docs/TASKS.md` und dieses Handoff lesen.
- Jede Aufgabe auf einem Feature-Branch abschließen: testen, committen, Branch pushen und PR gegen `main` erstellen.
- Niemals ohne ausdrückliche Nutzerbestätigung mergen oder Auto-Merge aktivieren.
- Datei-Schreibzugriffe ausschließlich über den getesteten ChangeSet-/Approval-Vertrag führen.
- Keine freie Shell; echter Loopback-Modellaufruf erst nach vollständigem MVP-2.B-Sicherheitsreview.
- Neue Architekturentscheidungen im Decision Log ergänzen.
- Tests für negative Sicherheitsfälle vor Happy-Path-Komfort priorisieren.
- Modellantworten in MVP 2 immer als untrusted input behandeln; nur deterministischer Core und Tool-Policies dürfen Aktionen autorisieren.

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

> Lies docs/MASTER_PLAN.md vollständig und nutze ihn als strategische Quelle. Lies danach README.md, docs/SECURITY.md, docs/DECISIONS.md, docs/TASKS.md und docs/HANDOFF.md. Implementiere MVP 2.B als abgesicherten Loopback-HTTP-Adapter für lokale OpenAI-kompatible Modellserver. Erlaube ausschließlich kanonische Loopback-URLs und explizite Ports, deaktiviere Redirects und geerbte Proxies, setze harte Timeouts und Größenlimits und teste alle negativen Netzwerkfälle. Keine Remote-Endpunkte, Zugangsdaten, Tool-Autorität oder freie Shell.
