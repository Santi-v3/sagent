# Agent API

Lokale FastAPI für die erste technische Minimalversion von Sagent.

## Endpunkte

- `GET /health` – lokaler Service-Status
- `POST /agent/task` – deterministische Platzhalterantwort auf eine Aufgabe

Die API führt keine Dateioperationen, Shell-Befehle, Modellaufrufe oder externen Netzwerkzugriffe aus.

## Start

Vom Repository-Root:

```bash
uv run uvicorn sagent_agent_api.main:app --app-dir apps/agent-api/src --reload --host 127.0.0.1 --port 8765
```

## Tests

```bash
uv run pytest apps/agent-api/tests
```
