# Aufgaben

Aktueller Ausführungsausschnitt aus [`MASTER_PLAN.md`](MASTER_PLAN.md), Abschnitt 25. Jede Aufgabe bleibt klein genug für einen überprüfbaren Branch und Pull Request.

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

## Als Nächstes – MVP 1.C

- [ ] `WorkspaceGuard` mit kanonischer Pfadauflösung definieren
- [ ] Absolute Pfade, Traversal, Symlink-Ausbrüche und sensible Dateien blockieren
- [ ] `FileTool` für Lesen, Auflisten, Erstellen und Ändern hinter dem Guard entwerfen
- [ ] `ChangeSet` mit alten/neuen Inhalten und Unified Diff implementieren
- [ ] Schreibzugriffe an inhaltsgebundene Freigabe koppeln
- [ ] Negative Sicherheitstests und erlaubten Happy Path ergänzen

## Noch blockiert bis zu den Sicherheitsinkrementen

- Dateiänderungen bleiben blockiert, bis Guard, ChangeSet und Approval in MVP 1.C vollständig getestet sind
- Testbefehle erst nach MVP 1.D und einer expliziten Allowlist
- Git-Schreibaktionen erst nach MVP 1.E
- Echte LLMs und Netzwerkzugriff erst ab MVP 2

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
