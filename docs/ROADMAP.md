# Roadmap

Die vollständige strategische Roadmap steht in [`MASTER_PLAN.md`](MASTER_PLAN.md). Dieses Dokument übersetzt sie in kompakte, ausführbare Lieferinkremente. Alle Schritte des Developer-Agent-Flows gehören gemeinsam zu **MVP 1**.

## Phase 0 – Foundation abgeschlossen

- Monorepo und Dokumentationssystem angelegt
- Sicherheits- und Approval-Grundsätze festgelegt
- TypeScript- und Python-Tooling vorbereitet
- Masterplan als kanonische Kontextquelle verankert

## MVP 1.A – Lokale API und Web-Grundgerüst

**Status: abgeschlossen**

- FastAPI-App mit `GET /health` und simuliertem `POST /agent/task`
- Strukturierte Antworten ohne Modellaufruf
- pytest-Tests für beide Endpunkte
- Einfache Next.js-Oberfläche für Task-Eingabe und Antwort
- Lokale Startanleitung und Lockfiles

**Grenze:** Keine Dateioperationen, Shell-Befehle oder echten LLM-Aufrufe.

## MVP 1.B – Simulierter Developer-Agent-Workflow

**Status: abgeschlossen**

- `TaskPlanner`, `ChangeProposal` und `ApprovalState`
- Plan-, Task- und Approval-Endpunkte
- Plan-, Risiko- und Approval-Anzeige in der UI
- Tests für Zustandsübergänge und ungültige Freigaben

**Grenze:** Der Workflow plant nur und verändert keine Dateien.

## MVP 1.C – WorkspaceGuard, Dateien und Diffs

**Status: abgeschlossen**

- Kanonische Workspace-Grenze und Schutz sensibler Pfade
- Begrenzte Datei-Tools hinter dem WorkspaceGuard
- ChangeSet und Unified Diff
- Schreiben ausschließlich nach inhaltsgebundener Freigabe
- Negative Tests für Traversal, Symlinks, `.env` und Workspace-Ausbruch

## MVP 1.D – Sichere Test-Ausführung

**Status: abgeschlossen**

- Allowlist-basierter TestRunner ohne freie Shell
- Strukturierte, begrenzte Testresultate
- API- und UI-Darstellung
- Tests für Erfolg, Fehler, Timeout und verbotene Befehle

## MVP 1.E – Git-Diff und Branch-Workflow

**Status: abgeschlossen**

- Strukturierter Git-Status, aktueller Branch und begrenzter, redigierter Diff
- Lokale Feature-Branch-Erstellung mit enger Namensregel und Zustandsvergleich
- Nicht ausführende Commit-Vorbereitung, gebunden an einen sichtbaren Diff-Hash
- Push und Merge im Agent-Tool blockiert; kein Merge ohne ausdrückliche Freigabe
- Git-Ansicht in der Weboberfläche und negative Sicherheitsprüfungen
- Sicherheits-, Workflow- und Handoff-Dokumentation aktualisiert

**MVP 1 abgeschlossen:** Die Kriterien aus Abschnitt 28 des Masterplans wurden am 2026-06-29 gegen Implementierung, Tests und lokale Startprüfung auditiert.

## MVP 2 – Echtes LLM und Modell-Router

- **MVP 2.A abgeschlossen:** provider-neutraler Modellvertrag, deterministischer Fake-Adapter, Capability-Router und Transport-Allowlist
- **MVP 2.B abgeschlossen:** abgesicherter opt-in Loopback-Adapter sowie begrenzte, aktiv abbrechbare Modelljobs
- **MVP 2.C Grundstein implementiert:** feste synthetische Aufgaben, prompt-freie Metriken und standardmäßig blockierte opt-in Benchmark-CLI
- **MVP 2.C Live-Schritt offen:** reproduzierbare Evaluation mit bewusst gestarteten LM-Studio-/Ollama-Instanzen und bereits vorhandenen Modellen
- Adapter für lokale OpenAI-kompatible Endpunkte
- LM Studio, Ollama und später MLX evaluieren
- Coding-Modelle anhand reproduzierbarer Aufgaben vergleichen
- Sicherheitsentscheidungen bleiben vollständig außerhalb des Modells

## MVP 3 – Memory V2

- Lokale Embeddings und semantische Suche evaluieren
- Qdrant oder Chroma anhand klarer Kriterien auswählen
- Projektwissen, Entscheidungen und Task-Historie auffindbar machen

## MVP 4 – Datei- und Recherche-Agent

- Dokument- und Tabellenauswertung
- Kontrollierte Web-Recherche mit Quellen
- Browser-Tool und Rechercheberichte

## MVP 5 – Alltagstools

- E-Mail-Entwürfe, Kalender, Erinnerungen und To-dos
- Tages- und Wochenzusammenfassungen
- Externe Aktionen immer mit gesonderter Freigabe

## MVP 6 – Voice und Telefonie

- Speech-to-Text und Text-to-Speech
- Sprachnachrichten und Anrufskripte
- Echte Telefonie erst nach Kosten-, Datenschutz- und Sicherheitsprüfung
