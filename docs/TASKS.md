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

- [ ] Provider-neutralen `ModelAdapter`-Vertrag mit strukturierten Ein- und Ausgaben definieren
- [ ] Deterministischen Fake-Adapter für Tests und Offline-Entwicklung implementieren
- [ ] Lokalen OpenAI-kompatiblen Adapter ohne fest eingebettete Zugangsdaten entwerfen
- [ ] LM Studio und Ollama anhand von Installation, API-Kompatibilität, Streaming und Mac-Ressourcen vergleichen
- [ ] Modelltext strikt als nicht vertrauenswürdige Eingabe behandeln; Tool-Policies bleiben deterministisch
- [ ] Timeout, Abbruch, fehlerhafte Antworten und nicht erreichbaren lokalen Modellserver testen
- [ ] Erst nach separater Freigabe einen echten lokalen Modellaufruf in API und UI aktivieren

## Noch blockiert bis zu den Sicherheitsinkrementen

- Dateiänderungen bleiben außerhalb des internen Core-Services blockiert, bis API- und UI-Anbindung einen eigenen Sicherheitsreview erhalten
- Testbefehle ausschließlich über die implementierte Allowlist und nach menschlicher Freigabe
- Git-Commit, Push und Merge bleiben ohne eigenen Approval-Flow blockiert
- Echte lokale LLM-Aufrufe und lokaler Netzwerkzugriff erst nach dem MVP-2-Vertrags- und Sicherheitsreview

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
