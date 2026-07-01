# Handoff

## Projektstatus

- **Phase:** MVP 1, MVP 2.A und MVP 2.B abgeschlossen; MVP 2.C Benchmark-Grundstein implementiert
- **Stand:** 2026-07-01
- **Repository:** `Santi-v3/sagent`
- **Aktueller Fokus:** Ersten Ollama-Live-Negativtest diagnostizieren; vor jeder Wiederholung Ollama und `gemma4:latest` außerhalb von Sagent manuell prüfen

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
- Transportklassen `in_process`, `loopback_http` und `remote_http` modelliert; die Standard-Allowlist erlaubt ausschließlich `in_process`
- Deterministischen `FakeModelAdapter` ohne Modell-, Netzwerk- oder Tool-Aufruf für Chat und Coding ergänzt
- `ModelRouter` mit festen Capability-Routen, Part-/Input-/Output-Limits, Streaming-Gate und Response-Identity-Prüfung implementiert
- Modellantworten unveränderlich als `untrusted=true` modelliert; der Adaptervertrag enthält keine Tool-Call- oder Policy-Schnittstelle
- `GET /models` und `POST /models/preview` für Discovery und begrenzte Offline-Simulation ergänzt
- 14 fokussierte Core-/API-Tests für Determinismus, Injection-Text, Limits, Routing, blockierte echte Adapter/Transporte und fehlerhafte Adapterantworten erfolgreich geprüft
- Kanonische `LoopbackEndpoint`-Policy für das exakte IPv4-Literal `127.0.0.1`, `/v1` und feste LM-Studio-/Ollama-Ports implementiert
- `LoopbackOpenAIChatAdapter` für nicht streamende `POST /v1/chat/completions` ohne Credentials, Proxies, Redirects, HTTP/2, Tools oder Retries ergänzt
- Source-labelled Inputs auf minimale System-/User-Messages abgebildet und Modell-, Request- sowie Response-Bytes begrenzt
- Strikte Response-Prüfung für Content-Type, UTF-8/JSON, Modell-ID, genau eine Assistant-Choice, Textinhalt, Finish-Reason und Usage implementiert
- `SAGENT_NETWORK_ENABLED=loopback` plus festes Provider-, Base-URL- und Modellprofil als vierfaches Opt-in eingeführt; Standardroute bleibt Fake
- `POST /models/complete` benötigt registrierten Loopback-Adapter und `confirmed=true`; URL, Port und Modell sind nicht request-steuerbar
- Positive Mock-Integration sowie negative Tests für URL-Ausbruch, Proxyvererbung, Redirect, Timeout, Connection-Fehler, Protokollfehler und Größenlimits ergänzt
- `docs/LOCAL_MODELS.md` mit Konfiguration, Sicherheitsgrenzen und noch offener Live-Evaluation ergänzt
- 38 fokussierte Loopback-/Model-API-Tests und insgesamt 107 Python-Tests erfolgreich geprüft; Ruff, ESLint, TypeScript und Produktionsbuild bestanden
- Thread-sicheren `ModelCancellationToken` mit idempotenten Close-Callbacks und eigenem `ModelCancelledError` implementiert
- Cancellation durch Router, Fake und Loopback-Adapter propagiert; aktiver Abbruch schließt HTTP-Client und Response-Stream
- Begrenzten `ModelJobService` mit einem API-Worker, maximal 100 Jobs und Zuständen `queued`, `running`, `cancelling`, `succeeded`, `failed`, `cancelled` ergänzt
- `POST /models/jobs`, `GET /models/jobs/{id}` und `POST /models/jobs/{id}/cancel` implementiert
- Job-Snapshots prompt-frei gehalten, interne Requests nach Terminalstatus verworfen und Adapterfehler generisch redigiert
- Race-, Queue-, Capacity-, Success-, Failure-, wiederholte Cancel- und aktive Stream-Close-Fälle in Core und API getestet
- 61 fokussierte Model-/Cancellation-Tests und insgesamt 121 Python-Tests erfolgreich; Ruff, ESLint, TypeScript, Python-Kompilierung, Produktionsbuild und API-Shutdown geprüft
- Reproduzierbaren lokalen Benchmark-Plan in `docs/LOCAL_MODEL_BENCHMARKS.md` mit festen Providerprofilen, Sicherheitsregeln, Metriken und manuellen Befehlen dokumentiert
- Drei harmlose, versionierte synthetische Aufgaben für Refactor-Plan, Testfälle und Cancellation-Probe definiert
- Opt-in Benchmark-Harness und CLI ergänzt: ohne `--confirmed` kein Routerbau, mit Bestätigung weiterhin vollständige Loopback-Prozesskonfiguration erforderlich
- Benchmark-Berichte auf Task-ID, Status, Zeit-/Längenmetriken, Untrusted-/Cancellation-Flags und generische Fehlercodes begrenzt; weder Prompt noch Modelltext werden ausgegeben
- Harness- und CLI-Tests ausschließlich mit Mock-Transports umgesetzt; kein echter Modellaufruf, keine Installation und kein Download durchgeführt
- 9 fokussierte Benchmark-Harness-/CLI-Tests und insgesamt 130 Python-Tests erfolgreich; Ruff, ESLint, TypeScript, Python-Kompilierung und Produktionsbuild bestanden
- Read-only Benchmark-Sektion in der Weboberfläche ergänzt: Harness-Status, exakte Loopback-Provider, drei feste Task-IDs, sicherer unbestätigter CLI-Aufruf und Datenschutzgrenzen
- Start-Button bewusst deaktiviert; keine Benchmark-API-Route, keine Providerprüfung und keine automatische Ausführung beim Seitenladen ergänzt
- Statischen UI-Sicherheitsvertrag mit Node-Bordmitteln getestet: nur erlaubte Provider, fester Task-Katalog, kein `--confirmed`, keine Ergebnistextfelder und kein Netzwerkpfad in der Komponente
- Python-/Web-Vertragstest ergänzt, der Providerprofile und feste Ports aus der Routerkonfiguration, Task-IDs aus dem Core-Katalog sowie Befehl und read-only UI-Grenzen deterministisch abgleicht
- Der Vertragstest liest ausschließlich versionierte lokale Dateien und importiert bestehende Konstanten; keine Runtime-Kopplung, API-Route, Providerprüfung oder Netzwerkaktion ergänzt
- 4 fokussierte Offline-Vertragstests, 4 bestehende UI-Sicherheitschecks und insgesamt 134 Python-Tests erfolgreich; Ruff, ESLint, TypeScript, Python-Kompilierung und Next.js-Produktionsbuild bestanden
- Öffentliche `LOCAL_PROVIDER_PROFILES` als Tuple aus unveränderlichen Profilen ergänzt; IDs, Labels, Adapter-IDs, IPv4-Loopback-Host und Ports liegen damit im Core statt in einer privaten API-Dict
- Router, Benchmark-Allowlist und Offline-Vertragstest lesen dieselben Core-Metadaten; die Web-App behält ihre statische JSON-Datei und erhält keine Python-Runtime-Abhängigkeit
- 4 neue Core-Metadaten-Tests, 4 Offline-Vertragstests, 4 UI-Sicherheitschecks und insgesamt 138 Python-Tests erfolgreich; Ruff, ESLint, TypeScript, Python-Kompilierung und Next.js-Produktionsbuild bestanden
- `docs/OLLAMA_LIVE_BENCHMARK_RUNBOOK.md` als rein manuelle Vorbereitung für den ersten Ollama-Lauf ergänzt; nur `127.0.0.1:11434` und bereits lokal vorhandene Modelle sind zulässig
- Cloud-Modelle, das Suffix `:cloud`, `glm-5.2:cloud`, automatische Installation, `ollama pull`, `ollama run`, Downloads und Providererkennung im Runbook ausdrücklich ausgeschlossen
- Getrennte Freigabepunkte für die spätere exakte Modellwahl und einen einzelnen `--confirmed`-Lauf sowie CLI-/API-Abbruchwege und prompt-/antworttextfreie Datenregeln dokumentiert
- Ersten bestätigten Ollama-Live-Benchmark mit `gemma4:latest` ausschließlich auf `127.0.0.1:11434` ausgeführt; beide regulären Tasks endeten ohne Modelloutput mit `reachable=false` und `local_model_job_failed`
- `cancellation-probe` nach etwa 120 Sekunden wirksam abgebrochen; keine Prompts oder Modellantworttexte gespeichert, keine Tool-Autorität, Downloads, Cloud- oder Remote-HTTP-Nutzung
- Lauf als sicheren Negativtest statt Modellvergleich eingeordnet; Worktree blieb anschließend sauber

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
- Standardmäßig bleibt die Modellvorschau ein In-Process-Fake; echter Netzwerkzugriff ist ausschließlich als explizit konfigurierter und bestätigter IPv4-Loopback-Aufruf möglich
- Datei-Tools sind noch nicht an API oder UI angebunden; ChangeSet-Zustände bleiben im Prozessspeicher
- Mehrdatei-ChangeSets sind pro Datei atomar, aber noch keine globale Dateisystemtransaktion
- Testprozesse haben noch keine echte macOS-Dateisystem-/Netzwerk-Sandbox; nur bewusst geprüfte lokale Workspaces ausführen
- Tasks und Verlauf sind noch nicht persistent
- Git-Status und Diff sind an dieses Repository gebunden; eine sichere Workspace-Auswahl ist noch nicht implementiert
- Die Commit-Vorbereitung ist nur ein unveränderlicher Plan. Sagent kann selbst weder stagen noch committen, pushen oder mergen
- Secret-Erkennung ist absichtlich konservativ und musterorientiert; ein Treffer blockiert die Commit-Vorbereitung, ersetzt aber keinen manuellen Secret-Scan
- Die visuelle Git-Ansicht wurde im laufenden Feature-Branch geprüft; der isolierte `main`-Browserdurchlauf wurde durch wiederholte Unterbrechungen der lokalen Browserverbindung nicht vollständig automatisiert. API- und Tool-Tests decken `main`-Warnung und Branch-Wechsel ab
- `remote_http` bleibt immer blockiert; `loopback_http` ist nur nach vollständiger Prozesskonfiguration und bestätigtem Request aktiv
- Es gibt noch kein Streaming, keine automatische Modellserver-Erkennung und keinen echten Modellvergleich
- Modelljobs sind nur prozesslokal; API-Neustart verwirft Status und Ergebnis
- Cancellation ist für den nicht streamenden HTTP-Job umgesetzt, aber noch nicht in der Weboberfläche sichtbar
- Die Kompatibilität ist gegen die offiziellen LM-Studio-/Ollama-Verträge und Mock-Transports geprüft; der erste Ollama-Live-Lauf lieferte jedoch keinen erfolgreichen Modelloutput
- Ein bestätigter Live-Benchmark wurde als sicherer Negativtest durchgeführt; ein Qualitätsvergleich wurde nicht durchgeführt und darf daraus nicht abgeleitet werden
- Benchmark-Ausgabe ist absichtlich flüchtig; eine persistente Ergebnisablage benötigt einen eigenen Datenschutz- und Redaction-Review
- Die Weboberfläche zeigt Benchmark-Metadaten nur statisch; sie kann keinen Benchmark starten und prüft keinen Providerstatus
- Python und Web behalten getrennte Runtime-Metadaten; ein Offline-Test stoppt bei Drift, ohne eine neue Laufzeitabhängigkeit zwischen beiden Stacks einzuführen

## Nächster sinnvoller Schritt

Den fehlgeschlagenen ersten Lauf vor jeder weiteren Sagent-Ausführung manuell eingrenzen:

1. Nutzer prüft lokal außerhalb von Sagent, ob Ollama läuft und `gemma4:latest` direkt erreichbar ist; Sagent führt diesen Providercheck nicht aus.
2. Ist das Modell nicht direkt erreichbar, wird kein Sagent-Benchmark wiederholt und es erfolgt keine automatische Reparatur oder Installation.
3. Nur bei positivem manuellen Befund darf der Nutzer später genau einen weiteren Lauf mit denselben festen Loopback-Werten ausdrücklich bestätigen.
4. Auch dann werden ausschließlich prompt- und antworttextfreie Metriken ausgewertet; ein Qualitätsvergleich benötigt erfolgreiche, separat freigegebene Läufe.

Kostenpflichtige APIs, externe Modellendpunkte, freie Shell und Modell-gesteuerte Policy-Entscheidungen bleiben ausdrücklich ausgeschlossen.

## Wichtige Leitplanken für die nächste Session

- Zuerst `docs/MASTER_PLAN.md`, danach `docs/SECURITY.md`, `docs/DECISIONS.md`, `docs/TASKS.md` und dieses Handoff lesen.
- Jede Aufgabe auf einem Feature-Branch abschließen: testen, committen, Branch pushen und PR gegen `main` erstellen.
- Niemals ohne ausdrückliche Nutzerbestätigung mergen oder Auto-Merge aktivieren.
- Datei-Schreibzugriffe ausschließlich über den getesteten ChangeSet-/Approval-Vertrag führen.
- Keine freie Shell, kein Remote-Modell und keine automatische Installation oder Modell-Downloads.
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

> Lies docs/MASTER_PLAN.md, docs/LOCAL_MODELS.md, docs/LOCAL_MODEL_BENCHMARKS.md und docs/OLLAMA_LIVE_BENCHMARK_RUNBOOK.md vollständig, danach SECURITY.md, DECISIONS.md, TASKS.md und HANDOFF.md. Der erste bestätigte Ollama-Lauf mit `gemma4:latest` war ein sicherer Negativtest ohne erfolgreichen Modelloutput. Führe keinen weiteren Benchmark oder Providercheck aus. Der Nutzer prüft zunächst außerhalb von Sagent manuell, ob Ollama und das Modell direkt erreichbar sind. Nur bei positivem Befund und neuer ausdrücklicher Bestätigung ist später genau ein weiterer Lauf zulässig. Installiere oder lade nichts. Keine Remote-Endpunkte, Zugangsdaten, Tool-Autorität oder freie Shell.
