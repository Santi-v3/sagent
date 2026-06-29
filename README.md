# Sagent

Sagent ist ein local-first, Mac-first Personal AI Agent in Entwicklung. Langfristig soll er wie ein eigener Coding-Agent arbeiten: Projekte lesen, Änderungen planen, Code vorbereiten, Tests ausführen, Diffs erklären und Änderungen erst nach ausdrücklicher menschlicher Freigabe übernehmen.

Das Repository enthält eine erste lokal ausführbare Minimalversion: eine deterministische Agent-API und eine einfache Codex-nahe Weboberfläche. Es gibt weiterhin keine LLM-Anbindung und keine Datei-, Shell- oder Systemwerkzeuge.

## Projektkontext

[`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md) ist die kanonische Quelle für Vision, Zielbild, MVP-Reihenfolge und langfristigen Funktionsumfang. Die fokussierten Dokumente konkretisieren den Masterplan:

1. `docs/DECISIONS.md` hält später getroffene Architekturpräzisierungen fest.
2. `docs/SECURITY.md` enthält verbindliche Schutzregeln; bei Unklarheit gilt die strengere Regel.
3. `docs/TASKS.md` und `docs/HANDOFF.md` beschreiben den aktuellen Arbeitsstand.

Bei Widersprüchen wird nichts stillschweigend überschrieben: Die Abweichung wird dokumentiert und vor der Implementierung geklärt.

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
  web/           Lokale Next.js-Oberfläche
  agent-api/     Lokale FastAPI mit Task-, Plan- und Approval-Workflow
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
- pnpm 11 oder neuer
- Python 3.12
- uv

## Installation

```bash
pnpm install
uv sync --dev
```

Optional kann `.env.example` nach `.env` kopiert werden. Für den Standardstart sind keine Secrets oder API-Keys erforderlich.

## Lokal starten

API und Weboberfläche gemeinsam starten:

```bash
pnpm dev
```

Danach sind verfügbar:

- Weboberfläche: `http://127.0.0.1:3000`
- API-Status: `http://127.0.0.1:8765/health`
- Interaktive API-Dokumentation: `http://127.0.0.1:8765/docs`

Die API kann auch separat gestartet werden:

```bash
uv run uvicorn sagent_agent_api.main:app \
  --app-dir apps/agent-api/src \
  --reload \
  --host 127.0.0.1 \
  --port 8765
```

## Qualität prüfen

```bash
pnpm check
pnpm build
```

`pnpm check` führt ESLint, ruff, TypeScript-Prüfung und pytest aus.

## Dokumentation

- [Masterplan](docs/MASTER_PLAN.md)
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

**MVP 1.B abgeschlossen.** Sagent erzeugt deterministische Pläne mit Ziel, Schritten, Risiken, nächsten Aktionen und Änderungsvorschlag. Freigeben, Ablehnen und Überarbeitung anfordern funktionieren über API und Codex-nahe UI. Als Nächstes folgt MVP 1.C mit WorkspaceGuard, sicheren Dateioperationen und Diffs; weiterhin ohne LLM-Aufrufe.

## Lizenz

Noch nicht festgelegt. Bis eine Lizenzdatei hinzugefügt wird, bleiben alle Rechte vorbehalten.
