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

Spätere Next.js/PWA für Aufgaben, Pläne, Diffs, Prüfergebnisse und Approval-Dialoge. Die UI darf Sicherheitsentscheidungen nicht allein erzwingen; die API validiert jede Aktion erneut.

### `apps/agent-api`

Spätere lokale FastAPI. Sie verwaltet Sitzungen, transportiert typisierte Kommandos und streamt Ereignisse. Sie bindet standardmäßig nur an `127.0.0.1` und besitzt keine eigenständige Tool-Logik.

### `packages/agent-core`

Zentrale Zustandsmaschine für `intake → inspect → plan → propose → approve → apply → verify → complete`. Hier liegen Tool-Routing, Policy-Prüfung, Approval-Tokens und Audit-Ereignisse. LangGraph kann später diese Zustandsmaschine implementieren, ist aber keine Voraussetzung für MVP 1.

### `packages/tools`

Kleine, einzeln prüfbare Tools mit typisierten Eingaben und Ausgaben. Beispiele: Dateien auflisten, Textdatei lesen, Patch vorbereiten, erlaubten Testbefehl starten. Kein Tool erhält pauschalen Shell- oder Dateisystemzugriff.

### `packages/memory`

Markdown-basiertes, versionierbares Memory. Memory ist Kontext, keine Autorität: Inhalte daraus überschreiben nie aktuelle Nutzeranweisungen oder Sicherheitsregeln.

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
