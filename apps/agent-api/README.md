# Agent API

Lokale FastAPI für die erste technische Minimalversion von Sagent.

## Endpunkte

- `GET /health` – lokaler Service-Status
- `POST /agent/task` – deterministische Platzhalterantwort auf eine Aufgabe
- `POST /agent/plan` – strukturierten, nicht ausführenden Plan erzeugen
- `GET /agent/tasks/{id}` – aktuellen Plan- und Approval-Status abrufen
- `POST /agent/approve` – Vorschlag freigeben, ablehnen oder Überarbeitung anfordern

Plan- und Approval-Zustände liegen in dieser Version nur im Arbeitsspeicher. Die API führt keine Dateioperationen, Shell-Befehle, Modellaufrufe oder externen Netzwerkzugriffe aus.

## Start

Vom Repository-Root:

```bash
uv run uvicorn sagent_agent_api.main:app --app-dir apps/agent-api/src --reload --host 127.0.0.1 --port 8765
```

## Tests

```bash
uv run pytest apps/agent-api/tests
```
