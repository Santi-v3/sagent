# Lokale Modelle

Sagent unterstützt in MVP 2.B einen bewusst kleinen OpenAI-kompatiblen Vertrag für lokale Chat Completions. Der Adapter ist standardmäßig deaktiviert und kann ausschließlich einen vorkonfigurierten Server unter der exakten IPv4-Loopback-Adresse ansprechen.

## Unterstützte Profile

| Profil | Erlaubte Base-URL | Vertrag |
| --- | --- | --- |
| LM Studio | `http://127.0.0.1:1234/v1` | `POST /v1/chat/completions` |
| Ollama | `http://127.0.0.1:11434/v1` | `POST /v1/chat/completions` |

Die Ports entsprechen den Beispielen der offiziellen [LM-Studio-Dokumentation](https://lmstudio.ai/docs/developer/openai-compat/chat-completions) und [Ollama-Dokumentation](https://docs.ollama.com/api/openai-compatibility). Andere Hosts, Hostnamen, Ports, Pfade, Protokolle, Redirects und Remote-Endpunkte werden abgewiesen.

## Aktivierung

Sagent lädt keine `.env`-Datei automatisch. Die folgenden vier Werte müssen im selben Prozesskontext explizit gesetzt werden:

```bash
export SAGENT_NETWORK_ENABLED=loopback
export SAGENT_LLM_PROVIDER=lm-studio
export SAGENT_LLM_BASE_URL=http://127.0.0.1:1234/v1
export SAGENT_LLM_MODEL=your-local-model-identifier
```

Für Ollama werden Provider und Port angepasst:

```bash
export SAGENT_NETWORK_ENABLED=loopback
export SAGENT_LLM_PROVIDER=ollama
export SAGENT_LLM_BASE_URL=http://127.0.0.1:11434/v1
export SAGENT_LLM_MODEL=your-local-model-identifier
```

Danach wird die API neu gestartet. `GET /models` zeigt den registrierten Adapter, aber niemals Base-URL oder Zugangsdaten.

## Expliziter lokaler Aufruf

Ein echter lokaler Aufruf erfolgt nur über `POST /models/complete`, einen registrierten `local-*`-Adapter und `confirmed=true`:

```json
{
  "adapter_id": "local-lm-studio",
  "prompt": "Erstelle einen kleinen, prüfbaren Refactor-Plan.",
  "capability": "coding",
  "max_output_tokens": 256,
  "confirmed": true
}
```

Die Antwort bleibt `untrusted=true`. Sie ist Textdaten und autorisiert keine Datei-, Shell-, Git-, Netzwerk- oder Tool-Aktion.

## Abbrechbare Jobs

Für längere Generierungen ist der Job-Flow vorgesehen:

1. `POST /models/jobs` mit demselben Adapter, Prompt, Capability, Tokenlimit und `confirmed=true` liefert `202` und eine `job_id`.
2. `GET /models/jobs/{job_id}` liefert ausschließlich prompt-freie Metadaten, Status und gegebenenfalls das untrusted Ergebnis.
3. `POST /models/jobs/{job_id}/cancel` setzt den Job auf `cancelling`, schließt den aktiven HTTP-Client und Response-Stream und endet in `cancelled`.

Terminale Jobs können nicht nachträglich abgebrochen werden. Ein bereits abgebrochener Job akzeptiert wiederholtes Cancel idempotent. Es gibt maximal einen Worker und 100 gespeicherte Jobs im API-Prozess; alte terminale Jobs werden bei Bedarf verworfen.

## Sicherheitsgrenzen

- Nur das exakte Literal `127.0.0.1`; kein IPv6, `localhost`, DNS oder alternative IP-Darstellung.
- Nur `http`, der Profilport und der kanonische Pfad `/v1`.
- Keine URL-Credentials, Query-Parameter, Fragmente, API-Keys oder `Authorization`-Header.
- Keine geerbten Proxyvariablen, Redirects, HTTP/2, automatischen Retries oder Tool-Definitionen.
- Feste Connect-, Read-, Write- und Pool-Timeouts sowie Request-/Response-Byte-Limits.
- Nur genau eine textuelle Assistant-Antwort mit `finish_reason=stop|length`; Tool-Calls, mehrere Choices, falsche Modell-ID und ungültige Usage werden verworfen.
- Adapter-, Modell- und Request-Identität werden im `ModelRouter` erneut geprüft.

## Noch nicht abgeschlossen

- Live-Evaluation mit einem tatsächlich gestarteten LM-Studio- und Ollama-Server
- reproduzierbarer Vergleich von Qwen3-Coder, Devstral und weiteren Open-Weight-Coding-Modellen
- Streaming und Jobsteuerung aus der Weboberfläche
- Modellwahl in der Weboberfläche
- sichere Unterstützung abweichender lokaler Ports oder authentifizierter Server
- MLX-Adapter

Bis zur Live-Evaluation bleibt der deterministische Fake der Standardroute. Jobzustände liegen nur im Arbeitsspeicher und gehen beim API-Neustart verloren.

Der sichere, noch nicht live ausgeführte Versuchsplan und die opt-in CLI stehen in [`LOCAL_MODEL_BENCHMARKS.md`](LOCAL_MODEL_BENCHMARKS.md).
