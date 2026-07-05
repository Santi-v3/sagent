# Agent API

> **Pflegebereich:** API-Gruppen, Start und lokale Laufzeitgrenzen. Einzelne Schemas sind unter `/docs` sichtbar.

Die lokale FastAPI bindet standardmäßig an `127.0.0.1:8765`.

## API-Gruppen

- Health und Capability-Preview
- deterministischer Task-, Plan- und Approval-Workflow
- Agent Loop als normale Antwort und SSE-Stream
- klassischer TestRunner sowie neuer Preview-/Approve-/Run-Testfluss
- Git-Status, Diff und lokale Branch-Erstellung
- Modell-Discovery, Offline-Preview, Completion, Streaming und Jobs
- Code-Edit Preview, Approval und Apply
- Memory speichern, suchen, auflisten und löschen
- deaktivierte Cloud-Approval- und Config-Previews

## Zustände

Plan-, Approval-, Test-, ChangeSet- und ModelJob-Zustände sind überwiegend prozesslokal. Memory wird in SQLite persistiert.

## Sicherheitsgrenze

Die klassischen Code-Edit-, Test- und Git-Endpunkte nutzen enge Verträge. Die Agent-Loop-Endpunkte registrieren zusätzlich direkte Shell- und Dateiwerkzeuge und sind experimentell. Verbindliche Einschränkungen: [`docs/SECURITY.md`](../../docs/SECURITY.md).

## Start

```bash
PYTHONPATH=apps/agent-api/src:packages/tools/src:packages/agent-core/src:packages/memory/src \
  uv run uvicorn sagent_agent_api.main:app \
  --app-dir apps/agent-api/src \
  --reload \
  --host 127.0.0.1 \
  --port 8765
```

## Tests

```bash
uv run pytest apps/agent-api/tests
```
