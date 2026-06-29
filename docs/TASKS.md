# Aufgaben

Aktueller Ausführungsausschnitt aus [`MASTER_PLAN.md`](MASTER_PLAN.md), Abschnitt 23. Jede Aufgabe bleibt klein genug für einen überprüfbaren Branch und Pull Request.

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

## Als Nächstes – MVP 1.B

- [ ] Domänenmodelle für `TaskPlanner`, `ChangeProposal` und `ApprovalState` definieren
- [ ] Statuswerte `pending`, `approved`, `rejected`, `needs_changes` implementieren
- [ ] Endpunkte für Plan, Approval und Task-Status ergänzen
- [ ] Plan, Risiken und Approve/Reject in der UI anzeigen
- [ ] Zustandsübergänge und ungültige Approval-Werte testen

## Noch blockiert bis zu den Sicherheitsinkrementen

- Dateiänderungen erst nach MVP 1.C und getesteter Workspace-/Approval-Logik
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
