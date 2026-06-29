# Agent API

Lokale FastAPI für die erste technische Minimalversion von Sagent.

## Endpunkte

- `GET /health` – lokaler Service-Status
- `POST /agent/task` – deterministische Platzhalterantwort auf eine Aufgabe
- `POST /agent/plan` – strukturierten, nicht ausführenden Plan erzeugen
- `GET /agent/tasks/{id}` – aktuellen Plan- und Approval-Status abrufen
- `POST /agent/approve` – Vorschlag freigeben, ablehnen oder Überarbeitung anfordern
- `GET /agent/test-profiles` – feste lokale Test-Allowlist anzeigen
- `POST /agent/run-tests` – exakt angezeigtes Testprofil nach Task-Freigabe starten
- `GET /agent/test-results/{id}` – begrenztes, redigiertes Ergebnis abrufen

Plan-, Approval- und Testergebnis-Zustände liegen in dieser Version nur im Arbeitsspeicher. Die API führt keine Dateioperationen, freien Shell-Befehle, Modellaufrufe oder beabsichtigten externen Netzwerkzugriffe aus.

## Start

Vom Repository-Root:

```bash
PYTHONPATH=apps/agent-api/src:packages/tools/src:packages/agent-core/src \
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
