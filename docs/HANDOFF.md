# Handoff

## Projektstatus

- **Phase:** MVP 1, MVP 2.A, MVP 2.B, MVP 2.C und MVP 2.D (Code Edit Preview) abgeschlossen; Code-Edit UI Hardening + History abgeschlossen; Capability Policy Offline-Vertrag abgeschlossen; Capability Policy Preview API + UI abgeschlossen; Approval-Gated Test Runner abgeschlossen
- **Stand:** 2026-07-02
- **Repository:** `Santi-v3/sagent`
- **Aktueller Fokus:** Approval-gated Test Runner (erste echte Power-User-Fähigkeit) mit Preview → Approve → Run Flow; Capability-Policy-Gate; feste Allowlist; `remote_http` und Cloud-Ausführung bleiben blockiert

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
- `docs/CLOUD_PROVIDER_POLICY.md` als reines Sicherheits- und Architekturkonzept für spätere optionale Cloud-Provider ergänzt
- DeepSeek Cloud als eigenen, standardmäßig deaktivierten `remote_http`-Provider für große Coding-/Reasoning-Aufgaben eingeordnet; keine Vermischung mit Ollama, LM Studio oder Loopback
- Laufgebundene Nutzerfreigabe, sichtbares Datenmanifest, Datenminimierung, Secret-Ausschluss, fehlenden Local-to-Cloud-Fallback und untrusted Antworten ohne Tool-Autorität festgelegt
- Keine Cloud-Runtime, API-Route, Endpoint-, Modell- oder Secret-Konfiguration implementiert und keinen Cloud-/Provideraufruf durchgeführt

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
- Die Cloud-Provider-Policy ist ausschließlich ein Zielvertrag. `remote_http` bleibt technisch blockiert; DeepSeek ist nicht registriert und besitzt weder Endpoint noch API-Key-Konfiguration
- `CloudProviderDisabledError` als unabhängiger Guard jenseits der Transport-Allowlist implementiert; `ModelRouter` blockiert `remote_http` zusätzlich über `cloud_providers_enabled=False`
- 14 Cloud-Guard-Tests decken sechs Sicherheitsdimensionen ab: remote_http-Blockade, Provider-Allowlist, Impersonationsschutz, Fallback-Verbot, Tool-Autoritätsausschluss und Secret-Scan
- Offline-Cloud-Approval-Contract als reine Dataclass-Struktur in `cloud_approval.py` implementiert: `CloudApprovalRequest`, `CloudDataDisclosure`, `CloudApprovalDecision`, `is_cloud_approval_valid()`
- Validierungsregeln im Dataclass-`__post_init__` verankert: `secrets_excluded` darf nie False sein, `full_repo_dump` ist immer verboten, `explicit_confirmed=True` zwingend für approved, `scope` muss `one_run_only` sein, Provider-ID muss in `CLOUD_PROVIDER_IDS` enthalten sein
- 18 fokussierte Tests in `test_cloud_approval.py`: Default-Denial, Secrets-Verbot, Repo-Dump-Verbot, unbekannte/lokale Provider blockiert, gültige Freigabe erkannt, Approval erzeugt keinen Transport/Endpoint/API-Key
- `CloudApprovalPreview` als frozen Dataclass und `build_cloud_approval_preview()` als reine Offline-Transformationsfunktion ergänzt
- 11 Preview-Tests: denied by default, gültige Freigabe angezeigt, Disclosure-Felder, Risiko-Hinweise, keine Endpoints/API-Keys, kein Providerbau, keine Dateileserechte, frozen
- Lokale read-only API-Route `POST /cloud/approval-preview` ergänzt; sie transformiert ausschließlich sichere Metadaten und besitzt keinen Provider-, Datei- oder Netzwerkzugriff
- Statische Cloud-Approval-Preview-UI mit `Preview only`, `Local metadata only` und `Cloud execution: No` ergänzt
- UI über die bestehende lokale API-Basis an die Preview-Route angebunden; Request bleibt denied und enthält nur Provider-ID, Zweck, Bestätigungsflags und leere Disclosure-Metadaten
- API-Responses werden vor Anzeige erneut gegen den denied Vertrag geprüft; bei Fehler oder unerwarteter Response bleibt die versionierte JSON-Vorschau als sicherer Offline-Fallback sichtbar
- Das UI-Wiring führt keinen Cloud-Aufruf aus, aktiviert keinen Transport und akzeptiert weder Prompt-/Datei-/Diff-Inhalte noch Secrets oder Modellantworten
- `docs/CLOUD_APPROVAL_UX_RUNBOOK.md` dokumentiert den späteren `one_run_only`-UX-Flow, Pflichtanzeigen, harte Blocker, Ablauf der Freigabe, sichere Fehlerfälle und vollständig offline testbare Anforderungen
- Das Runbook ist reine Spezifikation: Es ergänzt weder Runtime- noch UI-Code und erteilt keine Cloud-, Provider-, Transport- oder Datenfreigabe
- Öffentliches `CloudProviderConfig`-Schema als unveränderlichen Offline-Vertrag ergänzt: nur bekannte Cloud-Provider-ID, immer deaktiviert, `remote_http` nur als Klassifikation, Approval-Scope `one_run_only` und kein konfigurierter Endpoint
- `CloudProviderConfigValidation` meldet Ausführung immer als blockiert; das Schema liest keine Umgebung, Secrets oder Endpoints, baut keinen Provider und verändert weder `cloud_providers_enabled` noch `allowed_transports`
- 23 fokussierte Cloud-Config-Tests und insgesamt 223 Python-Tests bestanden; Ruff und Python-Kompilierung bleiben grün
- Lokale read-only Route `GET /cloud/config-preview` ergänzt; sie bildet ausschließlich das statische disabled/not_configured Schema ab und baut weder Router noch Provider
- Cloud-Approval-Bereich zeigt Config-Status, blockierte Ausführung, blockiertes Remote-HTTP, fehlenden Endpoint-/Secretzugriff und `one_run_only`-Approval mit sicherem statischem Fallback
- 6 fokussierte Config-Preview-API-Tests, 18 Web-/UI-Sicherheitstests und insgesamt 229 Python-Tests bestanden; Ruff, ESLint, TypeScript, Python-Kompilierung und Next.js-Produktionsbuild bleiben grün

## Abgeschlossen – MVP 2.D (Code Edit Preview Panel)

- `code_edits.py`-Backend-Service mit deterministischer Preview (`sha256`-Hash aus Path/Content/Beschreibung), Hash-gebundener Approval und Apply-Simulation implementiert
- Drei API-Endpunkte in `main.py` ergänzt: `POST /agent/code-edits/preview`, `POST /agent/code-edits/approve`, `POST /agent/code-edits/apply`
- Jede API-Antwort deklariert `shell_executed=false`, `git_executed=false`, `network_used=false`, `model_authority=false` als Literal-Felder
- Proposal-Hash-Bindung: Approval/Apply erfordert exakten Hash aus der Preview; abweichende Hashes und Statuskonflikte werden mit 409 abgewiesen
- 16 API-Tests decken Preview-Validierung (leerer Pfad, leere Beschreibung), Approve/Apply-Erfolgs- und Fehlerpfade, doppelte Ausführung, Hash-Manipulation, Required-Flags und nonexistente ChangeSets ab
- `CodeEditPreviewPanel`-Webkomponente als read-only-first UI: Formular (Pfad, Inhalt, Beschreibung), Diff-Preview, Approval-Schaltfläche, Apply-Schaltfläche (erst nach erfolgreicher Approval aktiviert)
- Stale-Detection: Änderungen an Pfad oder Inhalt nach Preview setzen den Vorschlag als veraltet; Approve/Apply-Buttons werden deaktiviert
- Sicherheitsinvarianten in der Komponentenausgabe: Read-Only-Badge, ShieldCheck mit "Keine Shell · Kein Git · Kein Netzwerk · Kein Modell"
- 11 Web-Sicherheitstests: Komponentenname, erlaubte Endpoints, keine Cloud-/Shell-/Git-/Commit-/Push-/Merge-Schaltflächen, keine `model_response`- oder Secret-Felder, Stale-Detection-Prüfung
- Komponente in `sagent-shell.tsx` integriert, CSS in `globals.css`
- Linting, TypeScript, 55 Python-Tests, 11 Web-Tests und Next.js-Produktionsbuild erfolgreich

## Abgeschlossen – Code-Edit UI Hardening + History (PR #23)

- Panel-Statusanzeige mit sechs Zuständen: idle, preview_ready, previewing, approved, applied, stale, error
- Reset-Button in der Statusleiste (immer sichtbar, wenn nicht idle): löscht lokalen UI-State, Diff-Anzeige und proposal_hash; führt keine API-Apply-Aktion aus
- Lokale UI-History (Browser-State, keine Persistenz): zeigt die letzten 20 Aktionen als sichere Metadaten (action, timestamp, path, status, gekürzter proposal_hash)
- History speichert keine Datei-Inhalte, keine Secrets; kein localStorage/sessionStorage/IndexedDB
- Sichere Fehleranzeige: generische Meldungen, keine Stacktraces, keine sensiblen Inhalte
- Stale-Detection: Änderung an Pfad oder Inhalt invalidiert Approval, disabled Apply, zeigt stale-Status
- 8 neue Web-Sicherheitstests: Reset, History-Aktionen, History-Inhaltsfreiheit, proposal_hash-Kürzung, Stacktrace-Verbot, Stale-Detection, Storage-Freiheit
- Insgesamt 32 Web-Tests, 73 Python-Tests, ESLint, TypeScript, Ruff, Next.js-Build: alle grün
- Keine neuen Backend-Fähigkeiten, keine Cloud/DeepSeek/remote_http, keine Shell/Git/Network, keine Persistenz

## Abgeschlossen – Capability Policy Offline-Vertrag (PR #24)

- `CapabilityName`, `CapabilityMode`, `CapabilityDecision`, `CapabilityPolicy` als reine Offline-Dataclasses definiert
- `evaluate_capability()` als reine Funktion ohne Seiteneffekte implementiert
- `DEFAULT_CAPABILITY_POLICY` mit 12 Capability-Mode-Zuordnungen: `read_workspace=preview_only`, `preview_file_edits=allowed`, `apply_single_file_edit=approval_required`, `apply_multi_file_edit=approval_required`, `run_tests=approval_required`, `run_shell_command=approval_required`, `git_status=allowed`, `git_commit=approval_required`, `git_push=approval_required`, `change_dependencies=approval_required`, `use_local_model=approval_required`, `use_cloud_model=disabled`
- Validierung: unbekannte Capability-Namen und ungültige Modi werden mit `CapabilityPolicyError` abgewiesen; Policy ist frozen
- Approval-Gating: `approval_required` ohne Approval → DENIED, mit Approval → NEEDS_APPROVAL; `is_preview=True` → PREVIEW_ONLY
- Unbekannte Capabilities standardmäßig disabled/denied
- Entscheidungen enthalten keine URLs, Endpoints, Secrets, Executors, Adapter, Router, Transporte oder `model_response`-Felder
- Policy enthält keine Secrets, Env-Variablen, Endpoints, Provider oder Modell-Laufzeit-Referenzen
- 41 Tests in `test_capability_policy.py`: Default-Policy, Mode-Defaults, Evaluate-Logik, Seiteneffektfreiheit, Secret-/Env-Freiheit, Custom-Policy
- Insgesamt 255 Python-Tests, 32 Web-Tests, Ruff, ESLint, TypeScript, Next.js-Build: alle grün
- Keine Runtime-Aktivierung, keine API-Routen, keine Web-UI-Änderungen, keine Shell/Git/Network/Cloud/DeepSeek

## Abgeschlossen – Capability Policy Preview API + UI (PR #25)

- `GET /capabilities/preview` read-only Route in `main.py`: gibt alle 12 Capabilities mit Mode, Entscheidung, requires_approval/preview_only/disabled Booleans und Safety-Flags zurück
- `CapabilityPreviewResponse` und `CapabilityEntryResponse` Pydantic-Modelle in `models.py`
- Safety-Flags: `shell_executed=false`, `git_executed=false`, `network_used=false`, `cloud_used=false`, `model_called=false`, `runtime_activated=false`
- `policy_version: "1.0.0"` als statischer Literal-String
- 11 API-Tests: Status 200, 12 Capabilities, Safety-Flags, Mode-Prüfungen, keine Secrets/Endpoints/Env
- `CapabilityPolicyPreview` React-Komponente in `capability-policy-preview.tsx`
- Tabellarische Anzeige mit Capability-Name, Mode-Badge, Entscheidungs-Icons (Allowed/Needs Approval/Preview Only/Denied)
- Read-Only-Badge, Sicherheitshinweis (keine Runtime-Aktionen), Safety-Flags-Banner
- Statischer JSON-Fallback in `data/capability-policy-preview.json`
- API-Fehler → Fallback; AbortController für Race-Condition-Schutz
- 18 UI-Sicherheitstests: 12 Capabilities, Read-Only-Badge, Fallback, keine Toggle/Enable/Run/Shell/Git/Cloud/DeepSeek/API-Key/Endpoint/Secret/model_response/Storage
- CSS in `globals.css`: Tabellen-Layout, Badge, Safety-Banner, responsive
- Integration in `sagent-shell.tsx` unter BenchmarkStatus
- Insgesamt 266 Python-Tests, 47 Web-Tests, Ruff, ESLint, TypeScript, Next.js-Build: alle grün
- Keine Runtime-Aktivierung, keine Shell/Git/Network/Cloud, keine Settings-Persistenz, keine Toggles/Enable-Buttons

## Abgeschlossen – Approval-Gated Test Runner (PR #26)

- `GET /agent/test-runs/commands` — listet 4 Allowlist-Kommandos
- `POST /agent/test-runs/preview` (201) — Preview mit Capability-Policy-Entscheidung + approval_hash
- `POST /agent/test-runs/approve` (200) — Hash-gebundene Freigabe
- `POST /agent/test-runs/run` (200) — Ausführung nur nach Approval + Hash-Match
- Capability-Policy-Gate: `evaluate_capability(RUN_TESTS)` ergibt `decision` in Preview
- Feste Allowlist in `test_runner.py`: `python-pytest-all`, `python-pytest-capability`, `python-pytest-preview`, `python-lint`
- argv aus Allowlist-Tupeln, `shell=False`, `subprocess.Popen` mit Timeout (60–120s) und Output-Begrenzung (20 KB)
- Environment-Sanitisierung: Proxy-Block, keine Netzwerk-Variablen, Temp-Home
- SHA-256-Hash-Bindung: `test_run_id:command_id:approval_token`
- Lock schützt vor gleichzeitigen Läufen; completed-Runs sind nicht wiederholbar
- 39 Tests: Allowlist-Validierung, Preview, Approve, Execute, Safety, Capability Gate, Secret-Freiheit
- 305 Python-Tests, Ruff, Compile, Secret-Scan: alle grün
- **Keine Git-Kommandos**, keine Network/Install/Download-Kommandos in der Allowlist
- **Keine Secrets/Endpoints/Env** in Responses
- **Keine Runtime-Aktivierung** außerhalb der Approval-Kette
- **Keine Modell-Autorität** für Test-Kommandos

## Offline Memory- und Tool-Proposal-Grundlage

- Der unterbrochene DeepSeek/OpenCode-Arbeitsstand wurde vollständig als lokaler
  Stash gesichert und nicht ungeprüft übernommen.
- `packages/memory` stellt jetzt bestätigungspflichtige, begrenzte lokale Einträge,
  optionale explizite SQLite-Persistenz und injizierbare Embeddings bereit.
- Das Memory-Paket liest keine Umgebung, besitzt keinen HTTP-Client und kontaktiert
  weder Ollama noch andere Provider. Standardmäßig bleibt es rein prozesslokal.
- `ToolRegistry` kann nur untrusted Modelltext in einen SHA-256-gebundenen
  `ToolCallProposal` umwandeln. Es gibt keine Handler, kein Dispatch und keine
  Ausführungsautorität.
- Lokale Store-Routen für Preview, hashgebundenes Approval und bestätigtes Apply
  sind angebunden. Preview/Approval schreiben nichts; Apply ist einmalig und nutzt
  ausschließlich den prozesslokalen Default-Service.
- Secrets in Text/Metadaten, unbekannte Felder, falsche Hashes, fehlendes Approval
  und Replays werden blockiert. Responses bestätigen fehlenden Netzwerk-, Modell-
  und Persistenzzugriff.
- Keine Web-UI, Search-/Delete-Route, automatische Prompt-Anreicherung oder
  Agent-Loop-Ausführung wurden aktiviert.
- 17 neue fokussierte Tests und insgesamt 355 Python-Tests bestanden; Ruff ist grün.

Nächster Schritt ist ein eigener read-only Search/List-Vertrag. Eine UI-Anbindung
darf erst danach mit separaten Sicherheitschecks erwogen werden.

## Nächster sinnvoller Schritt

Approval-Contract, lokale Preview-Route und read-only UI-Wiring liegen vor. Nächste Schritte vor jeder Cloud-Implementierung:

1. Den im Cloud-Approval-UX-Runbook beschriebenen Ablauf auf Basis des deaktivierten Config-Schemas als rein lokalen negativen Testvertrag konkretisieren; noch keinen Transport freigeben.
2. DeepSeek-Vertrag, Datenschutz, Aufbewahrung und Kosten separat prüfen; noch nichts implementieren oder verbinden.
3. Provider-/Modell-Allowlist, Datenmanifest, Redaction, Secretbezug und doppelte Freigabebindung als getrennte negative Testverträge abschließen.
4. Approval-Contract erst nach eigenem Security-Review als zusätzliches Gate vor `remote_http` in den Router integrieren.
5. Erst danach einen standardmäßig deaktivierten Cloud-Adapter erwägen.

Kostenpflichtige APIs, externe Modellendpunkte, freie Shell und Modell-gesteuerte Policy-Entscheidungen bleiben ausdrücklich ausgeschlossen.

## Wichtige Leitplanken für die nächste Session

- Zuerst `docs/MASTER_PLAN.md`, danach `docs/SECURITY.md`, `docs/DECISIONS.md`, `docs/TASKS.md` und dieses Handoff lesen.
- Jede Aufgabe auf einem Feature-Branch abschließen: testen, committen, Branch pushen und PR gegen `main` erstellen.
- Niemals ohne ausdrückliche Nutzerbestätigung mergen oder Auto-Merge aktivieren.
- Datei-Schreibzugriffe ausschließlich über den getesteten ChangeSet-/Approval-Vertrag führen.
- Keine freie Shell, kein aktiviertes Remote-Modell und keine automatische Installation oder Modell-Downloads.
- `docs/CLOUD_PROVIDER_POLICY.md` ist für jede spätere Cloud-Arbeit verbindlich; Konzeptfreigabe ist keine Runtime- oder Datenfreigabe.
- `docs/CLOUD_APPROVAL_UX_RUNBOOK.md` spezifiziert nur den späteren Nutzerablauf; es aktiviert weder Approval noch Cloud-Ausführung.
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

> Lies docs/MASTER_PLAN.md und docs/CLOUD_PROVIDER_POLICY.md vollständig, danach LOCAL_MODELS.md, LOCAL_MODEL_BENCHMARKS.md, OLLAMA_LIVE_BENCHMARK_RUNBOOK.md, SECURITY.md, DECISIONS.md, TASKS.md und HANDOFF.md. Local-first bleibt Standard; `remote_http` ist weiterhin blockiert. DeepSeek Cloud ist nur eine spätere optionale Provider-Idee für große Coding-/Reasoning-Aufgaben, kein Ollama-Modell und kein automatischer Fallback. Implementiere oder verbinde nichts ohne eigenes Security-Inkrement. Keine Secrets, privaten Daten, Remote-Endpunkte, Tool-Autorität, Downloads oder freie Shell.
