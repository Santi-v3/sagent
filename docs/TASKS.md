# Aufgaben

Aktueller Ausführungsausschnitt aus [`MASTER_PLAN.md`](MASTER_PLAN.md), Abschnitt 27. Jede Aufgabe bleibt klein genug für einen überprüfbaren Branch und Pull Request.

## Abgeschlossen – MVP 1.A

- [x] Root-Tooling installieren und Lockfiles erzeugen (`pnpm`, `uv`)
- [x] FastAPI-Grundstruktur in `apps/agent-api` anlegen
- [x] `GET /health` mit strukturierter Statusantwort implementieren
- [x] `POST /agent/task` als deterministische Simulation implementieren
- [x] pytest-Tests für `/health` und `/agent/task` ergänzen
- [x] Next.js-, React-, Tailwind- und TypeScript-Grundstruktur in `apps/web` anlegen
- [x] Task-Eingabe, Senden-Button, Antwort- und Fehleranzeige implementieren
- [x] Lokale Startanleitung in `README.md` ergänzen
- [x] Linting, Tests, Build und Browserfluss prüfen
- [x] `docs/HANDOFF.md` nach Abschluss aktualisieren

## Abgeschlossen – MVP 1.B

- [x] Domänenmodelle für `TaskPlanner`, `ChangeProposal` und `ApprovalState` definieren
- [x] Statuswerte `pending`, `approved`, `rejected`, `needs_changes` implementieren
- [x] Endpunkte für Plan, Approval und Task-Status ergänzen
- [x] Plan, Risiken und Approve/Reject in der UI anzeigen
- [x] Zustandsübergänge und ungültige Approval-Werte testen

## Abgeschlossen – MVP 1.C

- [x] `WorkspaceGuard` mit kanonischer Pfadauflösung definieren
- [x] Absolute Pfade, Traversal, Symlink-Ausbrüche und sensible Dateien blockieren
- [x] `FileTool` für Lesen, Auflisten, Erstellen und Ändern hinter dem Guard entwerfen
- [x] `ChangeSet` mit alten/neuen Inhalten und Unified Diff implementieren
- [x] Schreibzugriffe an inhaltsgebundene Freigabe koppeln
- [x] Negative Sicherheitstests und erlaubten Happy Path ergänzen

## Abgeschlossen – MVP 1.D

- [x] Allowlist für exakt definierte Testbefehle modellieren
- [x] `TestRunner` ohne `shell=True` und ohne frei übergebbare Argumente implementieren
- [x] Laufzeit-, Ausgabe- und Umgebungsgrenzen erzwingen
- [x] Strukturierte `TestResult`-Datensätze speichern
- [x] `POST /agent/run-tests` und `GET /agent/test-results/{id}` ergänzen
- [x] Teststatus und begrenzte Logs in der UI anzeigen
- [x] Erfolg, Fehler, Timeout und verbotene Befehle testen

## Abgeschlossen – MVP 1.E

- [x] `GitTool` für Status, aktuellen Branch und Diff als begrenzte Funktionen implementieren
- [x] Feature-Branch-Erstellung mit Warnung und Schutz für `main` ergänzen
- [x] Commit-Vorbereitung an exakten Diff-Hash und unveränderten Zustand koppeln
- [x] Push und Merge im Agent-Tool blockieren
- [x] `GET /git/status`, `GET /git/diff` und `POST /git/branch` ergänzen
- [x] Branch-, Status- und Diff-Informationen in der UI anzeigen
- [x] `main`-Schutz, Diff-Redaction, verbotenen Push/Merge und erlaubten Feature-Branch testen
- [x] Abschlusskriterien aus Abschnitt 28 des Masterplans auditieren

## Als Nächstes – MVP 2

- [x] Provider-neutralen `ModelAdapter`-Vertrag mit strukturierten Ein- und Ausgaben definieren
- [x] Deterministischen Fake-Adapter für Tests und Offline-Entwicklung implementieren
- [x] Capability-Router mit fester Transport-Allowlist und Input-/Output-Grenzen implementieren
- [x] Modellantworten unveränderlich als untrusted markieren und Tool-Call-Strukturen ausschließen
- [x] Adapter-Discovery und deterministische Offline-Preview in der API bereitstellen
- [x] Lokalen OpenAI-kompatiblen Adapter ohne fest eingebettete Zugangsdaten implementieren
- [x] Loopback-Literale, Providerports, Redirects, Proxies und Request-/Response-Größen absichern
- [x] Bestätigten `POST /models/complete` ohne frei wählbaren Endpoint bereitstellen
- [ ] LM Studio und Ollama anhand von Installation, API-Kompatibilität, Streaming und Mac-Ressourcen vergleichen
- [x] Reproduzierbaren Benchmark-Plan mit festen synthetischen Aufgaben und Metrikdefinitionen dokumentieren
- [x] Opt-in Benchmark-CLI mit `--confirmed`, bestehender Loopback-Konfiguration und prompt-freier Metrikausgabe implementieren
- [x] Benchmark-Harness ausschließlich mit Mock-Transports deterministisch testen
- [x] Sicheren Benchmark-Status, feste Provider und synthetische Aufgaben read-only in der Weboberfläche anzeigen
- [x] Offline-Vertragstest für Providerprofile, Task-IDs und read-only UI-Grenzen ergänzen
- [x] Lokale Providerprofile als öffentliche unveränderliche Core-Metadaten definieren
- [x] Sicheres manuelles Ollama-Runbook für einen später separat bestätigten ersten Live-Benchmark dokumentieren
- [x] Modelltext strikt als nicht vertrauenswürdige Eingabe behandeln; Tool-Policies bleiben deterministisch
- [x] Timeout, Redirect, Connection-Fehler, fehlerhafte Antworten und übergroße lokale Responses testen
- [x] Aktiven Abbruch einer bereits laufenden Modellgenerierung implementieren und testen
- [x] Begrenzte ModelJobs mit queued/running/cancelling/terminalen Zuständen bereitstellen
- [x] Prompt-freie Status-, Result- und Cancel-Endpunkte implementieren
- [x] Echten lokalen Modellaufruf ausschließlich als expliziten, bestätigten API-Opt-in aktivierbar machen
- [ ] Live-Aufruf mit LM Studio und Ollama auf dem Ziel-Mac prüfen
- [x] Ersten echten Benchmark nach bewusster Provider-/Modellvorbereitung und ausdrücklicher Nutzerbestätigung ausführen; Ergebnis war ein sicherer Negativtest ohne Modelloutput
- [ ] Außerhalb von Sagent manuell prüfen, ob Ollama läuft und `gemma4:latest` direkt erreichbar ist; bei negativem Befund keinen Sagent-Benchmark wiederholen
- [ ] Nur bei positivem manuellem Erreichbarkeitsbefund später genau einen weiteren Benchmark erneut ausdrücklich bestätigen
- [ ] Modellwahl, Jobstatus und Abbruch nach Live-Evaluation in die UI integrieren

## Cloud-Provider – Policy vor Implementierung

- [x] Local-first Cloud-Provider-Policy mit Datenklassifikation und fehlendem automatischem Fallback dokumentieren
- [x] DeepSeek Cloud als späteren optionalen `remote_http`-Provider für große Coding-/Reasoning-Aufgaben architektonisch von Ollama und LM Studio trennen
- [x] Laufgebundenes Datenmanifest, explizite Nutzerfreigabe und fehlende Tool-Autorität als Mindestvertrag festlegen
- [x] Offline-Cloud-Provider-Guard als unabhängigen Testvertrag implementiert (`CloudProviderDisabledError`, `cloud_providers_enabled`-Flag)
- [x] 14 Cloud-Guard-Tests decken remote_http-Blockade, lokale Provider-Allowlist, Fallback-Verbot, Tool-Autoritätsausschluss und Secret-Scan ab
- [x] Offline-Cloud-Approval-Contract als reine Datenstruktur implementiert (`CloudApprovalRequest`, `CloudDataDisclosure`, `CloudApprovalDecision`)
- [x] Validierungsregeln: default denied, explicit_confirmed required, one_run_only scope, Secrets/Repo-Dumps verboten, kein remote_http-Zugriff durch Approval
- [x] 18 fokussierte Approval-Tests decken Disclosure-Regeln, Request-Vertrag, Decision-Gates, Gültigkeitsprüfung und Provider-Identity ab
- [x] CloudApprovalPreview als frozen Dataclass und build_cloud_approval_preview() als reine Offline-Transformationsfunktion ergänzt
- [x] 11 Preview-Tests: denied by default, gültige Freigabe, Disclosure-Felder, Risiken, keine Endpoints/API-Keys/Provider/Dateileserechte
- [x] Lokale read-only API-Route `POST /cloud/approval-preview` für reine Preview-Metadaten bereitgestellt
- [x] Statische read-only Cloud-Approval-Preview-UI mit versioniertem JSON-Fallback ergänzt
- [x] Preview-UI an die lokale Route angebunden: nur denied Metadaten, strikt validierte Response und sicherer Offline-Fallback
- [x] UI-Sicherheitschecks für lokalen Routenpfad, verbotene Prompt-/Datei-/Diff-/Secret-Daten und fehlende Cloud-Aktionen ergänzt
- [x] Späteren `one_run_only` Cloud-Approval-UX-Flow, Pflichtanzeigen, Blocker, Fehlerfälle und Offline-Testanforderungen im Runbook dokumentiert
- [x] Deaktiviertes Cloud-Config-Schema als unveränderlichen Offline-Vertrag ergänzt; keine Env-Werte, Secrets, Endpoints, Provider oder Router-Freigaben
- [x] 23 Cloud-Config-Tests decken Default-Denial, Providertrennung, fehlende Netzwerk-/Secretfelder und unveränderte Router-Gates ab
- [x] Disabled Cloud-Config als lokale read-only API-/UI-Preview mit strikt validierter Response und statischem Offline-Fallback sichtbar gemacht
- [x] Config-Preview-Sicherheitschecks decken fehlende Env-/Secret-/Endpointfelder, blockiertes `remote_http` und fehlende Startaktionen ab
- [ ] Vor jeder Implementierung DeepSeek-Vertrag, Datenschutz, Kosten, Aufbewahrung und feste Provider-/Modell-Allowlist separat prüfen
- [ ] Provider-spezifisches Remote-HTTP-Threat-Model und negative Offline-Tests entwerfen
- [ ] Lokale Secret-Verwaltung, Redaction und Freigabebindung separat implementieren und reviewen
- [ ] Ablaufende, manifestgebundene `one_run_only`-Freigabe zunächst als rein lokalen negativen Testvertrag spezifizieren; noch keinen Transport freigeben
- [ ] Erst nach eigenem Security-Review einen minimalen, standardmäßig deaktivierten Cloud-Adapter erwägen

## Abgeschlossen – Code Edit Preview Panel (MVP 2.D)

- [x] CodeEdit-Backend-Service mit deterministischer Preview, Hash-gebundener Approval und sicherer Apply-Simulation implementiert
- [x] Drei API-Endpunkte ergänzt: `POST /agent/code-edits/preview`, `POST /agent/code-edits/approve`, `POST /agent/code-edits/apply`
- [x] API-Antworten melden stets `shell_executed=false`, `git_executed=false`, `network_used=false`, `model_authority=false`
- [x] Proposal-Hash-Bindung: Approval/Apply erfordert exakten Hash aus der Preview
- [x] 16 API-Sicherheitstests für Preview-Validierung, Approve/Apply-Flows, Hash-Schutz, Statuskonflikte und Required-Flags
- [x] CodeEditPreviewPanel-Webkomponente mit Formular, Diff-Preview, Approval- und Apply-Button (read-only-first)
- [x] Stale-Detection: Pfad-/Inhaltsänderung nach Preview invalidiert die Freigabe
- [x] Read-Only-Badge und Sicherheitsinvarianten (Keine Shell · Kein Git · Kein Netzwerk · Kein Modell)
- [x] 11 Web-Sicherheitstests: keine Cloud-/Shell-/Git-/Commit-/Push-/Merge-Schaltflächen, keine `model_response`- oder Secret-Felder
- [x] Komponente in sagent-shell.tsx integriert, CSS in globals.css
- [x] Linting, TypeScript, Build, 55 Python-Tests und 11 Web-Tests erfolgreich

## Noch blockiert bis zu den Sicherheitsinkrementen

- Dateiänderungen bleiben außerhalb des internen Core-Services blockiert, bis API- und UI-Anbindung einen eigenen Sicherheitsreview erhalten
- Testbefehle ausschließlich über die implementierte Allowlist und nach menschlicher Freigabe
- Git-Commit, Push und Merge bleiben ohne eigenen Approval-Flow blockiert
- Remote-LLMs und allgemeiner Netzwerkzugriff bleiben blockiert; lokale Aufrufe nur über den geprüften Loopback-Vertrag
- Die Cloud-Policy ist nur Architektur: `remote_http`, DeepSeek, Endpoints, Secrets und Cloud-Routen bleiben bis zu separaten Sicherheitsinkrementen blockiert

## Definition of Done

Eine Aufgabe ist fertig, wenn:

- Akzeptanzkriterien oder Tests vorhanden sind,
- Sicherheitsauswirkungen geprüft wurden,
- Formatierung, Linting und Tests erfolgreich sind,
- neue Entscheidungen dokumentiert wurden,
- `docs/HANDOFF.md` bei relevantem Session-Fortschritt aktualisiert wurde,
- `git status`, Diff und Secret-/Privatdaten-Prüfung sauber sind,
- keine Secrets, generierten Artefakte oder persönlichen Daten eingecheckt wurden,
- ein klarer Conventional Commit auf dem Feature-Branch erstellt wurde,
- der Feature-Branch ohne Force-Push gepusht wurde,
- ein PR gegen `main` existiert oder Link und Anleitung dokumentiert sind,
- Branch, Commit, Push, PR, Tests, Dateien, Risiken und Worktree-Status berichtet wurden,
- kein Merge ohne ausdrückliche Nutzerbestätigung erfolgt ist.
