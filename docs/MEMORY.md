# Memory

## Memory V1 (Markdown-Dateien) – geplant

Ursprüngliches Konzept: Markdown-Dateien mit Frontmatter für stabile Entscheidungen, Projektkonventionen und Session-Zusammenfassungen. Noch nicht implementiert.

## Memory V2 (Vektor-Gedächtnis) – implementiert

Seit 2026-07-02 läuft das Vektor-Gedächtnis über `packages/memory/`.

### Architektur

- **Embedding-Modell:** `nomic-embed-text` via Ollama (`POST /api/embeddings`)
- **Speicher:** In-Memory-Liste von `MemoryEntry`-Objekten (flüchtig, API-Neustart löscht Einträge)
- **Suche:** Cosine Similarity in reinem Python (kein numpy, keine Vektor-DB)
- **API:** `apps/agent-api/src/sagent_agent_api/memory_api.py`

### API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|-------------|
| `POST` | `/memory/store` | Text + optionales Metadata speichern |
| `POST` | `/memory/search` | Semantische Suche mit Query-Text |
| `GET` | `/memory` | Alle Einträge listen |
| `DELETE` | `/memory/{entry_id}` | Eintrag löschen |

### Metadata

Jeder Eintrag kann beliebiges Metadata enthalten (z.B. `category`, `type`, `source`). Wird bei der Suche mit zurückgegeben.
### Noch nicht implementiert (für später)

- Markdown-Frontmatter-Import (Memory V1)
- Automatisches Speichern von Entscheidungen aus dem Agent-Workflow
- Qdrant oder Chroma als skalierbare Vektor-DB
- Cloud-Synchronisierung

## Regeln

- Memory-Schreibvorgänge benötigen eine sichtbare Freigabe.
- Sensible Daten, Secrets und vollständige Chat-Transkripte werden nicht gespeichert.
- Jeder Eintrag hat Herkunft, Zeitstempel und Status.
- Aktuelle Nutzeranweisungen und Sicherheitsregeln haben Vorrang.
- Veraltete oder widersprüchliche Einträge werden markiert, nicht still überschrieben.
- Nutzer können Inhalte lesen, bearbeiten und löschen.
