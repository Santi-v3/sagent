# Lokale Modelle

Sagent unterstützt in MVP 2.B einen bewusst kleinen OpenAI-kompatiblen Vertrag für lokale Chat Completions. Der Adapter ist standardmäßig deaktiviert und kann ausschließlich einen vorkonfigurierten Server unter der exakten IPv4- oder IPv6-Loopback-Adresse ansprechen.

## Unterstützte Profile

| Profil | Erlaubte Base-URL | Vertrag |
| --- | --- | --- |
| LM Studio | `http://127.0.0.1:1234/v1` oder `http://[::1]:1234/v1` | `POST /v1/chat/completions` |
| Ollama | `http://127.0.0.1:11434/v1` oder `http://[::1]:11434/v1` | `POST /v1/chat/completions` |

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

## Sicherheitsgrenzen

- Nur exakte Literale `127.0.0.1` und `::1`; kein `localhost`, DNS oder alternative IP-Darstellung.
- Nur `http`, der Profilport und der kanonische Pfad `/v1`.
- Keine URL-Credentials, Query-Parameter, Fragmente, API-Keys oder `Authorization`-Header.
- Keine geerbten Proxyvariablen, Redirects, HTTP/2, automatischen Retries oder Tool-Definitionen.
- Feste Connect-, Read-, Write- und Pool-Timeouts sowie Request-/Response-Byte-Limits.
- Nur genau eine textuelle Assistant-Antwort mit `finish_reason=stop|length`; Tool-Calls, mehrere Choices, falsche Modell-ID und ungültige Usage werden verworfen.
- Adapter-, Modell- und Request-Identität werden im `ModelRouter` erneut geprüft.

## Noch nicht abgeschlossen

- Live-Evaluation mit einem tatsächlich gestarteten LM-Studio- und Ollama-Server
- reproduzierbarer Vergleich von Qwen3-Coder, Devstral und weiteren Open-Weight-Coding-Modellen
- Streaming und Abbruch aus der Weboberfläche
- Modellwahl in der Weboberfläche
- sichere Unterstützung abweichender lokaler Ports oder authentifizierter Server
- MLX-Adapter

Bis zur Live-Evaluation bleibt der deterministische Fake der Standardroute.
