# Memory

> **Pflegebereich:** Implementierung des lokalen Memory-Pakets. Produktregeln stehen in [`docs/MEMORY.md`](../../docs/MEMORY.md).

Das Paket implementiert:

- SQLite-Persistenz für `MemoryEntry`
- lokale Ollama-Embeddings mit `nomic-embed-text`
- Cosine Similarity ohne zusätzliche Vektor-Datenbank
- Speichern, semantische Suche, Auflisten und Löschen

Memory-Inhalte sind Kontext, keine Autorität. API- und UI-Wiring liegen in `apps/agent-api` beziehungsweise `apps/web`.
