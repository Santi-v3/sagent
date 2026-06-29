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
- `GET /git/status` – lokalen Branch und begrenzten Worktree-Status anzeigen
- `GET /git/diff` – begrenzten, Secret-redigierten Review-Diff anzeigen
- `POST /git/branch` – bestätigten lokalen Feature-Branch nach enger Namensregel erstellen
- `GET /models` – registrierte Adapter ohne Endpunkte oder Zugangsdaten anzeigen
- `POST /models/preview` – deterministische Offline-Antwort als ausdrücklich untrusted erzeugen
- `POST /models/complete` – bestätigten Textaufruf an einen explizit aktivierten Loopback-Adapter senden

Plan-, Approval- und Testergebnis-Zustände liegen in dieser Version nur im Arbeitsspeicher. Die Git-Endpunkte sind fest an den Repository-Root gebunden. Die Modellvorschau nutzt ausschließlich einen In-Process-Fake. Ein echter lokaler Modellaufruf benötigt `SAGENT_NETWORK_ENABLED=loopback`, ein festes LM-Studio-/Ollama-Profil und `confirmed=true`; Remote-Transporte bleiben blockiert. Die API führt keine Dateioperationen, freien Shell-Befehle, Pushes oder Merges aus.

Konfiguration und Sicherheitsgrenzen stehen in [`docs/LOCAL_MODELS.md`](../../docs/LOCAL_MODELS.md).

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
