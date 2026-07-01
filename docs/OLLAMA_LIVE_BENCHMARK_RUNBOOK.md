# Ollama Live-Benchmark Runbook

## Status und Zweck

Dieses Runbook bereitet den ersten kontrollierten Live-Benchmark von Sagent vor. Für
diesen ersten Test ist **Ollama** der empfohlene lokale Provider. Das ändert nicht den
sicheren Standardbetrieb: Ohne vollständige Loopback-Konfiguration bleibt der
deterministische In-Process-Fake aktiv.

Das Runbook ist ausschließlich eine manuelle Anleitung. Seine Aufnahme in das
Repository startet weder Ollama noch einen Providercheck, Modellaufruf oder Benchmark.
Der Nutzer muss später in einem separaten Schritt zuerst ein bereits lokal vorhandenes
Modell benennen und den einzelnen Benchmarklauf ausdrücklich bestätigen.

## Unveränderliche Sicherheitsgrenzen

- Erlaubter Provider: `ollama`
- Erlaubter Adapter: `local-ollama`
- Erlaubter Host: ausschließlich das IPv4-Literal `127.0.0.1`
- Erlaubter Port: ausschließlich `11434`
- Erlaubte Base-URL: ausschließlich `http://127.0.0.1:11434/v1`
- Keine Cloud-Modelle und keine Modellnamen mit dem Suffix `:cloud`
- `glm-5.2:cloud` ist für diesen Test ausdrücklich ausgeschlossen
- Keine Remote-Endpunkte, DNS-Namen, `localhost`, IPv6, Redirects oder Zugangsdaten
- Keine automatische Installation, kein `ollama pull` und kein Modell-Download
- Kein frei übergebbarer Prompt; die Benchmark-Harness nutzt nur den festen
  synthetischen Aufgabenkatalog
- Keine Tool-Definitionen und keine Tool-Autorität für Modellantworten

Ein Modell, das nicht bereits in der lokalen Ollama-Liste erscheint, ist für diesen
Benchmark nicht zugelassen. Es wird nicht im Rahmen dieses Runbooks nachinstalliert.

## Freigabepunkte

Der spätere Ablauf besitzt zwei getrennte menschliche Entscheidungen:

1. Der Nutzer führt die lokale Bestandsanzeige selbst aus und nennt anschließend die
   exakte ID eines bereits vorhandenen, nicht cloudbasierten Modells.
2. Erst nach dieser Modellauswahl bestätigt der Nutzer separat den Benchmarklauf. Das
   Flag `--confirmed` darf erst für genau diesen einzelnen Lauf verwendet werden.

Eine allgemeine Zustimmung zu Ollama ersetzt weder die konkrete Modellauswahl noch die
Bestätigung des Live-Benchmarks.

## Manuelle Checkliste vor einem späteren Lauf

- [ ] Ollama wurde vom Nutzer bereits installiert und bewusst lokal gestartet.
- [ ] Der gewählte Provider ist exakt `ollama`.
- [ ] Der Host ist exakt `127.0.0.1`; nicht `localhost`, IPv6 oder ein DNS-Name.
- [ ] Der Port ist exakt `11434`.
- [ ] Das Modell erscheint bereits in der lokalen Ausgabe von `ollama list`.
- [ ] Die Modell-ID endet nicht auf `:cloud`.
- [ ] Die Modell-ID ist nicht `glm-5.2:cloud`.
- [ ] Es wurde kein Modell installiert, gepullt oder automatisch heruntergeladen.
- [ ] Der Nutzer hat genau diese Modell-ID separat bestätigt.
- [ ] Der Nutzer bestätigt anschließend genau einen Benchmarklauf bewusst.
- [ ] Die vier `SAGENT_*`-Variablen enthalten nur die unten erlaubten Werte.
- [ ] Der Startbefehl enthält keine Provider-, URL-, Port- oder Prompt-Argumente.
- [ ] Ausreichend lokaler Arbeitsspeicher und ein Abbruchweg sind bekannt.

Wenn ein Punkt nicht eindeutig erfüllt ist, wird der Benchmark nicht gestartet.

## Schritt 1: Lokalen Modellbestand manuell anzeigen

Der Nutzer führt später selbst aus:

```bash
ollama list
```

Dieser Befehl ist nur zur manuellen Bestandsaufnahme vorgesehen. Aus der Spalte `NAME`
wird eine exakte Modell-ID ausgewählt, die bereits lokal vorhanden ist. Ein nicht
aufgeführtes Modell ist nicht zulässig. Insbesondere werden folgende Befehle in diesem
Runbook nicht verwendet:

```text
ollama pull ...
ollama run ...
```

`ollama run` ist ebenfalls ausgeschlossen, weil Ollama ein fehlendes Modell dabei
nachladen könnte. Sagent führt `ollama list` nicht selbst aus und erkennt Provider oder
Modelle nicht automatisch.

Nach der Bestandsaufnahme teilt der Nutzer die gewählte exakte Modell-ID separat zur
Prüfung mit. Bis zu dieser ausdrücklichen Auswahl wird kein weiterer Live-Schritt
ausgeführt.

## Schritt 2: Sagent-Prozessvariablen setzen

Erst nach der separaten Modellbestätigung wird im selben Terminal die Platzhalter-ID
durch die exakt bestätigte lokale Modell-ID ersetzt:

```bash
export SAGENT_NETWORK_ENABLED=loopback
export SAGENT_LLM_PROVIDER=ollama
export SAGENT_LLM_BASE_URL=http://127.0.0.1:11434/v1
export SAGENT_LLM_MODEL='REPLACE_WITH_CONFIRMED_LOCAL_MODEL_ID'
```

Der Modellwert muss exakt aus `ollama list` übernommen werden und darf weder auf
`:cloud` enden noch `glm-5.2:cloud` sein. Die Anwendung lädt keine `.env`-Datei
automatisch. Provider, URL, Port und Modell können nicht als Benchmark-CLI-Argumente
überschrieben werden.

## Schritt 3: Einen später ausdrücklich bestätigten Benchmark starten

Der folgende Befehl führt echte lokale Modellaufrufe aus und darf **nicht** während der
Vorbereitung verwendet werden. Er ist erst nach der separaten Nutzerbestätigung für
die gewählte Modell-ID zulässig:

```bash
PYTHONPATH=apps/agent-api/src:packages/agent-core/src:packages/tools/src \
  uv run python -m sagent_agent_api.benchmark_cli --confirmed
```

`--confirmed` bestätigt genau diesen Lauf. Die CLI akzeptiert keine Modell-ID, URL,
Provider-ID oder freien Prompts als Argument. Ohne `--confirmed` endet sie vor dem
Routerbau und vor jedem Netzwerkzugriff mit `confirmation_required`.

## Abbruch

### Gesamten CLI-Benchmark abbrechen

Der CLI-Benchmark veröffentlicht keine externe Job-ID. Ein laufender CLI-Prozess wird
im selben Terminal mit `Ctrl+C` abgebrochen. Beim Verlassen schließt die Harness ihre
internen Jobs und fordert für aktive Modellressourcen Cancellation an.

### Separaten API-Modelljob abbrechen

Nur falls unabhängig vom Benchmark bereits bewusst ein API-Modelljob gestartet wurde
und seine echte `job_id` bekannt ist, kann der vorhandene lokale Cancel-Endpunkt genutzt
werden:

```bash
curl --fail-with-body --request POST \
  http://127.0.0.1:8765/models/jobs/REPLACE_WITH_JOB_ID/cancel
```

Dieser API-Befehl gehört nicht zum normalen Benchmark-CLI-Ablauf. Es wird keine Job-ID
erfunden und kein neuer Job nur für einen Abbruch gestartet.

## Daten- und Vertrauensgrenzen

- Die Harness verwendet ausschließlich drei versionierte synthetische Aufgaben ohne
  Projekt-, Nutzer-, Memory- oder Secret-Inhalte.
- Der Prompt wird für den lokalen Aufruf nur im Prozessspeicher gehalten. Sagent
  schreibt ihn nicht in den Benchmark-Bericht oder eine Ergebnisdatei.
- Modellantworttext wird nur zur Laufzeit verarbeitet. Sagent persistiert und druckt
  ihn nicht; ausgegeben wird nur die begrenzte Zeichenanzahl.
- Der CLI-Bericht enthält Task-ID, Terminalstatus, Zeitmetriken, Erreichbarkeit,
  Antwortlänge, Untrusted-/Cancellation-Flags und generische Fehlercodes.
- Die CLI schreibt keine Ergebnisdatei. Eine manuelle Umleitung von stdout wäre eine
  separate Nutzeraktion und muss wie lokale Projektdaten behandelt werden.
- Sagent macht keine Aussage über unabhängige lokale Logs oder Speichermechanismen des
  vom Nutzer betriebenen Ollama-Prozesses.
- Jede Modellantwort bleibt `untrusted=true`. Sie autorisiert keine Datei-, Shell-,
  Git-, Netzwerk-, Approval- oder Tool-Aktion und wird nicht ausgeführt.

## Nach einem späteren Lauf

Die Prozessvariablen werden im selben Terminal entfernt:

```bash
unset SAGENT_NETWORK_ENABLED SAGENT_LLM_PROVIDER SAGENT_LLM_BASE_URL SAGENT_LLM_MODEL
```

Anschließend werden nur die prompt- und antworttextfreien Metriken sowie der lokale
Ressourcenverbrauch manuell geprüft. Ein zweiter Lauf, Providerwechsel, Modellwechsel
oder Qualitätsranking benötigt eine neue bewusste Entscheidung.

## Aktueller Abschlusszustand

Der erste ausdrücklich bestätigte Lauf wurde mit dem bereits lokal vorhandenen Modell
`gemma4:latest` über Ollama auf `127.0.0.1:11434` ausgeführt. Die beiden regulären
Aufgaben endeten ohne erfolgreichen Modelloutput mit `reachable=false` und dem
generischen Fehlercode `local_model_job_failed`. Die `cancellation-probe` wurde nach
etwa 120 Sekunden wirksam abgebrochen. Das ist ein sicherer Negativtest, kein
erfolgreicher Modellvergleich.

Es wurden weder Prompts noch Modellantworttexte gespeichert oder ausgegeben;
`prompt_stored` blieb `false`. Es gab keine Tool-Autorität, Downloads, Cloud- oder
Remote-HTTP-Nutzung. Der Worktree war nach dem Lauf sauber. Vor einem weiteren
Sagent-Benchmark muss der Nutzer außerhalb von Sagent manuell prüfen, ob Ollama läuft
und `gemma4:latest` direkt erreichbar ist. Ohne positiven manuellen Befund wird der
Benchmark nicht wiederholt; ein weiterer Lauf benötigt erneut eine ausdrückliche
Bestätigung.
