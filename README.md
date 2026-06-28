# Sagent

Sagent ist ein local-first, Mac-first Personal AI Agent in Entwicklung. Langfristig soll er wie ein eigener Coding-Agent arbeiten: Projekte lesen, Änderungen planen, Code vorbereiten, Tests ausführen, Diffs erklären und Änderungen erst nach ausdrücklicher menschlicher Freigabe übernehmen.

Dieses Repository enthält zunächst nur eine klare, dokumentierte Projektbasis. Es gibt noch keine LLM-Anbindung, keine produktive Benutzeroberfläche und keine Werkzeuge mit unbeschränktem Datei- oder Systemzugriff.

## Leitprinzipien

- **Local first:** Projekt- und Memory-Daten bleiben standardmäßig auf dem Gerät.
- **Human in the loop:** Schreibende oder ausführende Aktionen benötigen eine nachvollziehbare Freigabe.
- **Sichere Defaults:** Werkzeuge arbeiten in einem begrenzten Workspace und nach dem Prinzip der geringsten Rechte.
- **Diff statt Überraschung:** Jede vorgeschlagene Änderung wird vor der Anwendung sichtbar gemacht.
- **Kleine, prüfbare Schritte:** Sagent wächst über klar abgegrenzte MVPs statt über eine früh komplexe App.
- **Keine bezahlten Abhängigkeiten:** Die erste Basis funktioniert ohne kostenpflichtige APIs und ohne echte LLM-Aufrufe.

## Geplante Architektur

```text
apps/
  web/           Spätere Next.js/PWA-Oberfläche
  agent-api/     Spätere FastAPI für lokale Agent-Sitzungen
packages/
  agent-core/    Orchestrierung, Policies und Approval-Logik
  memory/        Markdown-basiertes Memory-System
  tools/         Begrenzte Datei-, Diff- und Test-Werkzeuge
  shared/        Gemeinsame Verträge und Hilfsfunktionen
docs/            Produkt-, Architektur- und Betriebsdokumentation
```

Der vorgesehene Stack ist Next.js, React, Tailwind und TypeScript im Frontend sowie Python, FastAPI, uv, pytest und ruff im Backend. pnpm Workspaces und Turborepo koordinieren das Monorepo. LangGraph ist erst für eine spätere Orchestrierungsphase vorgesehen.

## Voraussetzungen

- macOS
- Node.js 22 oder neuer
- pnpm 10 oder neuer
- Python 3.12 oder neuer
- uv

## Lokale Vorbereitung

Noch gibt es keine installierbaren App-Pakete. Sobald die ersten Scaffolds vorhanden sind, ist der vorgesehene Ablauf:

```bash
cp .env.example .env
pnpm install
uv sync --dev
pnpm check
```

## Dokumentation

- [Projektdefinition](docs/PROJECT.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Nächste Aufgaben](docs/TASKS.md)
- [Architekturentscheidungen](docs/DECISIONS.md)
- [Sicherheitsmodell](docs/SECURITY.md)
- [Memory-Konzept](docs/MEMORY.md)
- [Agent-Workflow](docs/AGENT_WORKFLOW.md)
- [Session-Handoff](docs/HANDOFF.md)

## Status

**Phase 0 – Foundation.** Die Repository-Struktur und die Projektverträge werden festgelegt. Der nächste technische Schritt ist ein minimaler, deterministischer Agent-Core ohne LLM, der einen Workspace nur lesen und einen Änderungsplan als Datenstruktur erzeugen kann.

## Lizenz

Noch nicht festgelegt. Bis eine Lizenzdatei hinzugefügt wird, bleiben alle Rechte vorbehalten.
