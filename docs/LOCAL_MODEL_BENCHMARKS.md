# Lokale Modell-Benchmarks

## Status und Ziel

Diese Datei definiert den reproduzierbaren Benchmark-Grundstein für MVP 2.C. Ein erster
ausdrücklich bestätigter Ollama-Live-Lauf wurde als sicherer Negativtest ausgeführt; er
lieferte keinen erfolgreichen Modelloutput. Die Harness vergleicht erst nach weiteren
separat bestätigten Läufen lokale LM-Studio-/Ollama-Instanzen anhand derselben harmlosen
synthetischen Aufgaben und gibt ausschließlich Metriken aus.

Nicht Teil dieses Schritts sind Installation, Modell-Download, automatische Provider-Erkennung, Remote-HTTP, Modellwahl, Qualitätsranking oder ein Default-Modell.

## Erlaubte lokale Provider

| Provider | Exakte Base-URL | Adapter-ID |
| --- | --- | --- |
| LM Studio | `http://127.0.0.1:1234/v1` | `local-lm-studio` |
| Ollama | `http://127.0.0.1:11434/v1` | `local-ollama` |

Alle anderen Hosts, IP-Darstellungen, Ports, Protokolle und Pfade bleiben gesperrt. Insbesondere sind `localhost`, IPv6, DNS, Redirects und `remote_http` nicht erlaubt.

## Sicherheitsvertrag

- Ohne `--confirmed` endet die CLI vor Routerbau und Netzwerkzugriff mit `confirmation_required`.
- Zusätzlich müssen die vier bestehenden `SAGENT_*`-Prozessvariablen ein gültiges Loopback-Profil bilden.
- Provider, URL, Port, Modell und Prompts können nicht als CLI-Argument überschrieben werden.
- Die Harness installiert oder startet keinen Provider und lädt kein Modell.
- Der Katalog enthält ausschließlich feste synthetische Prompts ohne Projekt-, Nutzer-, Memory- oder Secret-Daten.
- Modellantworten bleiben `untrusted=true`; ihr Text wird weder ausgeführt noch als Tool-Aufruf, Approval oder Policy-Entscheidung interpretiert.
- Der Adapter sendet keine Tool-Definitionen. Tool-/Function-Calls in Antworten werden weiterhin blockiert.
- Ausgabe enthält weder Prompt noch Modelltext. Es werden nur Task-ID, Status, Zeiten, Zeichenanzahl, Untrusted-Flag, Cancellation-Metriken und generische Fehlercodes ausgegeben.
- Die CLI schreibt keine Ergebnisdatei. Wer stdout später manuell speichert, muss den Inhalt weiterhin wie lokale Projektdaten behandeln.
- Ein Lauf verwendet einen Worker und höchstens so viele Job-Slots wie feste Aufgaben; die bestehenden Job-/Timeout-/Response-Limits bleiben aktiv.

## Manuelle Voraussetzungen

1. LM Studio oder Ollama wurde vom Nutzer bereits installiert.
2. Ein lokal vorhandenes Modell wurde vom Nutzer bewusst ausgewählt und geladen. Sagent lädt nichts herunter.
3. Der Provider wurde vom Nutzer auf seinem festen IPv4-Loopback-Port gestartet.
4. Repository-Abhängigkeiten wurden bereits mit `pnpm install` und `uv sync --dev` eingerichtet.
5. Vor jedem echten Lauf werden Modell-ID, freier Arbeitsspeicher und laufender Provider manuell geprüft.

## Synthetischer Aufgabenkatalog

| Task-ID | Zweck | Erwartete Behandlung |
| --- | --- | --- |
| `safe-refactor-plan` | Drei Schritte für das Refactoring einer eingebetteten reinen `clamp`-Beispielfunktion | Textantwort, keine Tools |
| `deterministic-test-cases` | Drei Tests für eine synthetische `add(a, b)`-Funktion | Textantwort, keine Dateien |
| `cancellation-probe` | Lange Liste harmloser Platzhalter | Nach Jobstart aktiv abbrechen |

Der Katalog ist im Code fixiert. Es gibt bewusst kein freies Prompt-Argument.

## Metriken

| Feld | Bedeutung |
| --- | --- |
| `reachable` | `true`, wenn eine gültige Completion empfangen wurde; `false` bei sicher fehlgeschlagenem Job; `null` bei bewusst abgebrochenem Probe-Job |
| `latency_ms` | Zeit von Job-Erstellung bis Worker-Start |
| `response_duration_ms` | Zeit von Worker-Start bis Terminalstatus |
| `total_duration_ms` | Gesamtdauer von Erstellung bis Terminalstatus |
| `status` | `succeeded`, `failed` oder `cancelled` |
| `cancellation_requested` | Ob die Harness für diese Aufgabe Cancel angefordert hat |
| `cancellation_effective` | Ob die Cancel-Aufgabe terminal `cancelled` wurde |
| `response_characters` | Antwortlänge ohne Speicherung des Antworttexts |
| `response_untrusted` | Muss bei einer erfolgreichen Antwort `true` sein |
| `prompt_stored` | Muss immer `false` bleiben |
| `error_code` | Nur generischer Code, niemals Provider- oder Modellfehlertext |

Nicht gemessen werden Qualität, Tokens pro Sekunde, Energieverbrauch oder Speicherbedarf. Diese Metriken benötigen einen späteren, separat freigegebenen Live-Evaluationsschritt.

## Erster Live-Negativtest

Der erste bestätigte Lauf verwendete `gemma4:latest` über Ollama ausschließlich auf
`127.0.0.1:11434`. `safe-refactor-plan` und `deterministic-test-cases` endeten mit
`reachable=false` und `local_model_job_failed`; es wurde kein erfolgreicher
Modelloutput empfangen. Die `cancellation-probe` wurde nach etwa 120 Sekunden wirksam
abgebrochen.

Damit ist die sichere Fehler- und Cancellation-Behandlung live belegt, aber weder
Provider-Kompatibilität noch Modellqualität. Aus diesem Lauf darf kein Qualitätsranking
abgeleitet werden. Prompts und Modellantworttexte wurden nicht gespeichert,
`prompt_stored` blieb `false`, und es entstand keine Tool-Autorität. Der Lauf nutzte
weder Downloads noch Cloud oder Remote-HTTP; der Worktree blieb sauber.

## Sicherer Standardaufruf

Dieser Aufruf führt keinen Benchmark und keinen Netzwerkzugriff aus. Er zeigt nur die blockierte, prompt-freie JSON-Antwort:

```bash
PYTHONPATH=apps/agent-api/src:packages/agent-core/src:packages/tools/src \
  uv run python -m sagent_agent_api.benchmark_cli
```

Erwarteter Exit-Code: `2`, erwarteter Fehlercode: `confirmation_required`.

## Manueller Lauf mit LM Studio

LM Studio und das bereits vorhandene Modell zuerst bewusst in der App starten. Danach im selben Terminal:

```bash
export SAGENT_NETWORK_ENABLED=loopback
export SAGENT_LLM_PROVIDER=lm-studio
export SAGENT_LLM_BASE_URL=http://127.0.0.1:1234/v1
export SAGENT_LLM_MODEL=your-already-installed-local-model

PYTHONPATH=apps/agent-api/src:packages/agent-core/src:packages/tools/src \
  uv run python -m sagent_agent_api.benchmark_cli --confirmed
```

## Manueller Lauf mit Ollama

Für den ersten späteren Ollama-Live-Lauf gilt zusätzlich das
[`OLLAMA_LIVE_BENCHMARK_RUNBOOK.md`](OLLAMA_LIVE_BENCHMARK_RUNBOOK.md). Es verlangt
eine getrennte Bestandsprüfung, Modellauswahl und Laufbestätigung und schließt
Cloud-Modelle sowie automatische Downloads aus.

Ollama und das bereits vorhandene Modell zuerst bewusst lokal starten. Danach im selben Terminal:

```bash
export SAGENT_NETWORK_ENABLED=loopback
export SAGENT_LLM_PROVIDER=ollama
export SAGENT_LLM_BASE_URL=http://127.0.0.1:11434/v1
export SAGENT_LLM_MODEL=your-already-installed-local-model

PYTHONPATH=apps/agent-api/src:packages/agent-core/src:packages/tools/src \
  uv run python -m sagent_agent_api.benchmark_cli --confirmed
```

Nach dem Lauf können die Prozesswerte entfernt werden:

```bash
unset SAGENT_NETWORK_ENABLED SAGENT_LLM_PROVIDER SAGENT_LLM_BASE_URL SAGENT_LLM_MODEL
```

## Reproduzierbarer Vergleich später

Ein späterer, ausdrücklich freigegebener Live-Vergleich verwendet für jede Provider-/Modellkombination:

1. denselben Commit,
2. denselben synthetischen Aufgabenkatalog,
3. dieselben Token-, Timeout- und Capacity-Limits,
4. einen kalten und mindestens drei warme Läufe,
5. nur die Metrik-JSON-Ausgabe ohne Prompt oder Modelltext,
6. eine manuelle Notiz zu Mac-Modell, RAM und bereits vorhandenem Modell.

Bis der Nutzer diesen Live-Schritt ausdrücklich startet, bleibt diese Harness ausschließlich offline mit Mock-Transports getestet.
