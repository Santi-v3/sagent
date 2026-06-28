# Roadmap

## Phase 0 – Foundation

- Monorepo und Dokumentation anlegen
- Sicherheits- und Approval-Verträge festlegen
- TypeScript- und Python-Tooling vorbereiten
- Definition of Done und Handoff-Routine etablieren

**Ergebnis:** Eine verständliche, valide Projektbasis ohne Laufzeitfunktionen.

## MVP 1 – Deterministischer Read-only Core

- Python-Paket für Session-, Plan- und Tool-Datentypen
- Workspace-Root und sichere Pfadauflösung
- Tools für Dateiliste und begrenztes Lesen von Textdateien
- Deterministischer Planner ohne LLM
- pytest-Tests für Traversal, Symlinks, Größenlimits und Binärdateien
- JSONL-Audit-Log

**Ergebnis:** Der Core kann einen Fixture-Workspace inspizieren und einen Plan erzeugen, aber nichts verändern.

## MVP 2 – Patch und Approval

- Änderungen ausschließlich als Unified Diff vorbereiten
- Patch-Validierung in isolierter Kopie
- Inhaltsgebundene Approval-Tokens
- Apply- und Reject-Ablauf
- Allowlist für Test- und Lint-Kommandos
- Rollback bei fehlgeschlagener Anwendung

**Ergebnis:** Ein deterministischer Vorschlag kann nach expliziter Freigabe sicher angewendet und geprüft werden.

## MVP 3 – Lokale API und minimale UI

- FastAPI-Endpunkte für Sessions, Events und Approvals
- Bindung nur an localhost
- Next.js-Oberfläche für Aufgabe, Plan, Diff und Freigabe
- Streaming von Status- und Prüfergebnissen
- Ende-zu-Ende-Test mit Fixture-Repository

**Ergebnis:** Der sichere Workflow ist über eine einfache lokale Weboberfläche nutzbar.

## MVP 4 – Lokales Modell und Memory

- Adapter-Schnittstelle für lokale Modelle
- Erste Integration über einen lokal betriebenen OpenAI-kompatiblen Endpoint
- Prompt-Injection-resistente Kontextaufbereitung
- Markdown-Memory mit Quellen, Gültigkeit und expliziter Schreibfreigabe
- Evaluations-Fälle für Planqualität und Tool-Auswahl

**Ergebnis:** Ein lokales Modell kann Vorschläge machen, ohne die Sicherheitsgrenzen zu kontrollieren.

## Später

- LangGraph-basierte Orchestrierung, wenn Zustandskomplexität sie rechtfertigt
- Native macOS-Integration und verbesserte Sandbox
- Git-Worktrees, Checkpoints und robuste Wiederaufnahme
- Erweiterbare, signierte Tool-Pakete
- Mehrere Projekte und optionale verschlüsselte Synchronisierung
