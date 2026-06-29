# Sagent

Sagent ist ein local-first, Mac-first Personal AI Agent in Entwicklung. Langfristig soll er wie ein eigener Coding-Agent arbeiten: Projekte lesen, Änderungen planen, Code vorbereiten, Tests ausführen, Diffs erklären und Änderungen erst nach ausdrücklicher menschlicher Freigabe übernehmen.

Das Repository enthält MVP 1 als lokal ausführbare Minimalversion und den ersten Baustein von MVP 2: eine deterministische Agent-API, eine Codex-nahe Weboberfläche, sichere ChangeSets, einen allowlist-basierten TestRunner, begrenzte Git-Funktionen sowie einen provider-neutralen Modellvertrag mit Offline-Fake und Transport-Allowlist. Es gibt weiterhin keinen echten LLM-Aufruf, keine freie Shell und keine unkontrollierten Systemwerkzeuge. Die Datei-Tools sind bewusst noch nicht mit API oder UI verbunden; Push und Merge sind im Agent-Tool nicht verfügbar.

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
  agent-core/    ChangeSets, Approval-Logik und provider-neutraler ModelRouter
  memory/        Markdown-basiertes Memory-System
  tools/         WorkspaceGuard, Datei-, Test- und begrenzte Git-Werkzeuge
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

Die Weboberfläche zeigt nach einer Task-Freigabe Testprofile sowie den lokalen Git-Status und den redigierten Diff. Einen neuen lokalen Branch kann sie nur mit den Präfixen `codex/`, `feature/`, `fix/`, `docs/`, `test/` oder `chore/` erstellen. Es gibt keine UI- oder API-Aktion für Push oder Merge.

Die API bietet außerdem `GET /models` und `POST /models/preview`. Beide verwenden ausschließlich den deterministischen In-Process-Fake. Loopback-HTTP, Remote-HTTP, Zugangsdaten und echte Modellserver sind in diesem Inkrement nicht aktiviert.

Die API kann auch separat gestartet werden:

```bash
PYTHONPATH=apps/agent-api/src:packages/tools/src:packages/agent-core/src \
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

**MVP 1 abgeschlossen; MVP 2.A in Arbeit.** Der lokale Workflow deckt Task-Planung, Proposal und Approval, sichere interne ChangeSets, allowlist-basierte Tests sowie redigierten Git-Status und Diff ab. Der neue `ModelRouter` trennt Fähigkeiten und Transportarten, bewahrt Eingabequellen und behandelt jede Modellantwort als untrusted. Aktuell ist ausschließlich ein deterministischer In-Process-Fake erlaubt. Als Nächstes folgt ein gesondert geprüfter Loopback-Adapter für lokale OpenAI-kompatible Modellserver.

## Lizenz

Noch nicht festgelegt. Bis eine Lizenzdatei hinzugefügt wird, bleiben alle Rechte vorbehalten.
