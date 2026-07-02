# Architektur

## Überblick

Sagent wird als lokales Monorepo mit klaren Vertrauensgrenzen aufgebaut. UI und API koordinieren Sitzungen; der Agent-Core entscheidet über Zustände und Policies; Tools führen ausschließlich eng definierte Aktionen aus.

```text
Web UI (untrusted input)
        |
        v
Agent API (session boundary)
        |
        v
Agent Core (state machine + policy + approval)
      /   \
     v     v
Memory   Tool Router
          |
          v
Sandboxed workspace tools
```

## Komponenten

### `apps/web`

Lokale Next.js-Oberfläche für Aufgaben, Pläne, Diffs, Prüfergebnisse und Approval-Dialoge. Seit MVP 1.E zeigt sie zusätzlich Branch, Worktree-Status und Git-Diff und kann einen policy-konformen lokalen Feature-Branch anfordern. Die UI darf Sicherheitsentscheidungen nicht allein erzwingen; die API validiert jede Aktion erneut.

### `apps/agent-api`

Lokale FastAPI. Sie verwaltet den derzeit flüchtigen Task-Workflow und transportiert typisierte Kommandos zu den eng begrenzten Tools. Sie bindet standardmäßig nur an `127.0.0.1` und besitzt keine eigenständige Tool-Logik.

### `packages/agent-core`

Zentrale Zustandsmaschine für `intake → inspect → plan → propose → approve → apply → verify → complete`. MVP 1.C implementiert hier unveränderliche ChangeSets, Unified Diffs, Proposal-Hashes und den einmaligen Approval-/Apply-Lebenszyklus. MVP 2.A ergänzt einen provider-neutralen `ModelRouter`, dessen Adapter ausschließlich untrusted Text erzeugen und keine Tool-Autorität erhalten. LangGraph kann später diese Zustandsmaschine implementieren, ist aber keine Voraussetzung für die bisherigen Inkremente.

### Modellgrenze in MVP 2.A

```text
source-labelled text parts
          |
          v
ModelRouter -- capability route --> allowed adapter transport
          |                              |
          |                        in_process only
          v                              v
limit + identity validation <--- untrusted text response
```

Die Standard-Transport-Allowlist enthält nur `in_process`. MVP 2.B kann nach expliziter Prozesskonfiguration zusätzlich genau einen `loopback_http`-Adapter für LM Studio oder Ollama registrieren. `remote_http` bleibt blockiert. Der Adaptervertrag kennt nur Text-Completion; Tool-Aufrufe, Dateioperationen, Shell und Policy-Entscheidungen sind nicht Teil der Schnittstelle.

Der Loopback-Adapter sendet den gemeinsamen OpenAI-kompatiblen Vertrag `POST /v1/chat/completions`. Endpoint, Providerprofil und Modell werden beim Routerbau fixiert. Ein API-Request kann diese Werte nicht verändern und muss den registrierten Adapter ausdrücklich mit `confirmed=true` auswählen.

Längere Aufrufe laufen optional als `ModelJob`: `queued → running → succeeded|failed` oder über `cancelling → cancelled`. Ein thread-sicherer Cancellation-Token wird durch Router und Adapter gereicht. Beim Cancel schließt er HTTP-Client und Response-Stream; Snapshots enthalten keine Prompts. Ein einzelner Worker und eine begrenzte In-Memory-Historie verhindern unbegrenzte Parallelität.

### `packages/tools`

Kleine, einzeln prüfbare Tools mit typisierten Eingaben und Ausgaben. MVP 1.C enthält den `WorkspaceGuard` und `FileTool` für begrenzte UTF-8-Textdateien. MVP 1.D ergänzt feste Testprofile, begrenzte Prozessausführung und redigierte Ergebnisse. MVP 1.E ergänzt repository-gebundenen Git-Status, begrenzte und redigierte Diffs, lokale Feature-Branch-Erstellung und eine nicht ausführende Commit-Vorbereitung. Schreibmethoden prüfen einen intern signierten Nachweis des Agent-Core erneut. Kein Tool erhält pauschalen Shell- oder Dateisystemzugriff; Git-Push und Merge sind nicht implementiert.

### `packages/memory`

Memory V1 bleibt menschenlesbar dokumentiert. Die MVP-3-Grundlage ergänzt einen
begrenzten lokalen Python-Service, typisierte Metadaten für Projektwissen,
Entscheidungen, Task-Historie und Zusammenfassungen sowie bestätigte Store-/Delete-
und read-only List/Search-Verträge. Memory ist Kontext, keine Autorität: Inhalte
daraus überschreiben nie aktuelle Nutzeranweisungen oder Sicherheitsregeln.

Der aktive Fallback verwendet prozesslokale Einträge, optional explizites SQLite
und deterministische Token-Suche. Qdrant Local Mode ist nur der bevorzugte Kandidat
für einen späteren synthetischen Vector-Store-Spike; keine Vector-Store-Abhängigkeit
oder Embedding-Runtime ist derzeit aktiviert.

### `packages/shared`

Sprachübergreifende Verträge werden zunächst als JSON-Schema dokumentiert und daraus später TypeScript- und Python-Typen abgeleitet. Keine Geschäftslogik.

## Daten- und Kontrollfluss

1. Nutzer wählt Workspace und formuliert Aufgabe.
2. API erzeugt eine Sitzung mit unveränderlicher Workspace-Grenze.
3. Core fordert nur die minimal notwendigen Lese-Tools an.
4. Core erzeugt einen strukturierten Plan und einen Patch-Vorschlag.
5. Policy Engine bewertet Pfade, Befehle und Auswirkungen.
6. UI zeigt Plan, Diff, Risiken und Prüfungen.
7. Eine zeitlich und inhaltlich gebundene Freigabe autorisiert exakt diesen Vorschlag.
8. Tool Router wendet den Patch in der Sandbox an und führt erlaubte Prüfungen aus.
9. Ergebnis und Audit-Ereignisse werden lokal gespeichert.

## Vertrauensgrenzen

- Nutzertext, Repository-Inhalte und Memory gelten als nicht vertrauenswürdig.
- Nur der Agent-Core darf Tool-Aufrufe autorisieren.
- Tools validieren Pfade und Argumente zusätzlich selbst.
- Die Sandbox ist eine technische Grenze; Approval ist eine separate Produktgrenze.
- API und UI erhalten nie geheime Werte zurück.

## Geplante Persistenz

- Projekt-Memory: Markdown im expliziten Sagent-Verzeichnis
- Sitzungsstatus: zunächst JSON/JSONL lokal, später optional SQLite
- Audit-Log: append-only JSONL mit redigierten Argumenten
- Keine Cloud-Persistenz in den ersten MVPs
