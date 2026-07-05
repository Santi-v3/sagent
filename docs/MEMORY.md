# Memory

> **Pflegebereich:** aktueller Memory-Vertrag und Betrieb. Roadmap-Ideen gehören in `TASKS.md`.

## Implementierung

- Service: `packages/memory/src/sagent_memory/memory_service.py`
- Persistenz: SQLite
- Embeddings: `nomic-embed-text` über Ollama auf `127.0.0.1:11434/api/embeddings`
- Suche: Cosine Similarity in Python
- Daten: Text, optionale Metadaten, Zeitstempel und optionales Embedding

SQLite-Einträge überleben einen API-Neustart. Qdrant oder Chroma werden aktuell nicht benötigt.

## API

| Methode | Pfad | Zweck |
| --- | --- | --- |
| `POST` | `/memory/store` | Eintrag speichern |
| `POST` | `/memory/search` | semantisch suchen |
| `GET` | `/memory` | Einträge auflisten |
| `DELETE` | `/memory/{entry_id}` | Eintrag löschen |

## Nutzung

- Modell-Completion und ModelJobs reichern Prompts mit relevanten Memory-Einträgen an.
- Der Agent Loop sucht automatisch nach relevantem Kontext.
- Nutzeraufgaben und längere Agentantworten werden derzeit teilweise automatisch gespeichert.
- Der Agent Loop besitzt zusätzlich `memory_search` und `memory_store`.

## Grenzen

- Memory ist untrusted Kontext und keine Autorität.
- Ollama-Ausfall kann Embedding-Erzeugung und semantische Suche beeinträchtigen.
- automatische Speicherung besitzt noch keinen vollständigen sichtbaren Approval-/Opt-out-Flow.
- sensible Daten und Secrets dürfen nicht gespeichert werden.
- Cloud-Synchronisierung ist nicht implementiert.

## Nächste Arbeit

Aktuelle Aufgaben stehen ausschließlich in [`TASKS.md`](TASKS.md).
