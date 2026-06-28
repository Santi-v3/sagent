# Handoff

## Projektstatus

- **Phase:** 0 – Foundation
- **Stand:** 2026-06-29
- **Repository:** `Santi-v3/sagent`
- **Aktueller Fokus:** Dokumentierte Monorepo-Basis und Sicherheitsverträge

## Fertiggestellt

- Monorepo-Verzeichnisse für Web, API, Agent-Core, Memory, Tools und Shared angelegt
- Root-Konfigurationen für pnpm, Turborepo und Python vorbereitet
- Produktvision, Architektur, Roadmap und konkrete Tasks dokumentiert
- Sicherheits-, Approval-, Memory- und Developer-Agent-Workflow festgelegt

## Bewusste Grenzen

- Noch keine installierten Dependencies oder Lockfiles
- Noch kein Next.js- oder FastAPI-Scaffold
- Noch kein ausführbarer Agent-Core
- Keine LLM- oder Netzwerk-Integration
- Keine Dateiänderungs- oder Shell-Tools

## Nächster sinnvoller Schritt

MVP 1 als read-only Python-Core beginnen:

1. `packages/agent-core` in ein uv-kompatibles `src/`-Paket überführen.
2. Domänenmodelle und eine explizite Zustandsmaschine definieren.
3. Sichere Workspace-Pfadauflösung testgetrieben implementieren.
4. Erst danach kleine `list_files`- und `read_text_file`-Tools ergänzen.

## Wichtige Leitplanken für die nächste Session

- `docs/SECURITY.md` und `docs/DECISIONS.md` vor Implementierungsänderungen lesen.
- Keine schreibenden Tools vor einem getesteten Proposal-/Approval-Vertrag.
- Keine freie Shell und keine echten LLM-Aufrufe.
- Neue Architekturentscheidungen im Decision Log ergänzen.
- Tests für negative Sicherheitsfälle vor Happy-Path-Komfort priorisieren.

## Startprompt für eine Folgesession

> Lies README.md, docs/SECURITY.md, docs/ARCHITECTURE.md, docs/TASKS.md und docs/HANDOFF.md. Implementiere den ersten read-only Agent-Core testgetrieben. Beginne mit Domänenmodellen und sicherer Workspace-Pfadauflösung; führe keine LLMs, Netzwerkzugriffe oder schreibenden Tools ein.
