# Lokale Modelle

> **Pflegebereich:** aktuelle Provider-, Aktivierungs- und Laufzeitgrenzen. Benchmarkabläufe stehen in den Benchmarkdokumenten.

## Unterstützte Profile

| Profil | Base-URL | Vertrag |
| --- | --- | --- |
| LM Studio | `http://127.0.0.1:1234/v1` | OpenAI-kompatible Chat Completions |
| Ollama | `http://127.0.0.1:11434/v1` | OpenAI-kompatible Chat Completions |

Andere Hosts, Ports, Redirects, Remote-Endpunkte und Request-Credentials werden abgewiesen.

## Aktivierung

```bash
export SAGENT_NETWORK_ENABLED=loopback
export SAGENT_LLM_PROVIDER=ollama
export SAGENT_LLM_BASE_URL=http://127.0.0.1:11434/v1
export SAGENT_LLM_MODEL=qwen2.5-coder:7b
```

Sagent lädt `.env` nicht automatisch. Modell, Provider und URL werden beim Routerbau fixiert und sind nicht frei pro Request steuerbar.

## Verfügbare Flüsse

- `GET /models`: registrierte Adapter anzeigen
- `POST /models/preview`: deterministische Offline-Preview
- `POST /models/complete`: bestätigte lokale Completion
- `POST /models/complete/stream`: lokale SSE-Completion
- `/models/jobs`: Job starten, Status lesen und abbrechen
- Model-Panel: Modellwahl, Jobstatus, Cancel und Ergebnis
- Chat: lokale Modellantwort, Streaming und Agent Loop

## Aktueller Live-Stand

Ollama wurde lokal mit `qwen2.5-coder:7b` für Chat, Coding, direkte Completion und Jobs erfolgreich geprüft. Weitere lokal vorhandene Modelle wurden erkannt. LM Studio wurde noch nicht gleichwertig verglichen und ist optional.

## Sicherheitsgrenzen

- exaktes IPv4-Literal `127.0.0.1`
- feste Profilports und kanonischer `/v1`-Pfad
- keine Credentials, Proxyvererbung, Redirects, HTTP/2 oder automatischen Retries
- Request-/Response-, Timeout- und Identitätsprüfung
- Modellantworten bleiben `untrusted=true`
- der Adapter selbst erhält keine Tool-Definitionen

Der experimentelle Agent Loop kann untrusted Modelltext anschließend als Tool-Call-Syntax interpretieren. Diese separate Risikogrenze steht in [`security/AGENT_LOOP.md`](security/AGENT_LOOP.md).

## Benchmarks

- Harness und Metriken: [`LOCAL_MODEL_BENCHMARKS.md`](LOCAL_MODEL_BENCHMARKS.md)
- Ollama-Runbook und erster Negativlauf: [`OLLAMA_LIVE_BENCHMARK_RUNBOOK.md`](OLLAMA_LIVE_BENCHMARK_RUNBOOK.md)
