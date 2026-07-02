# Memory V2: Vector-Store-Evaluation

Stand: 2026-07-02

## Ziel und Grenzen

Der Masterplan verlangt für MVP 3 eine begründete Auswahl zwischen Qdrant und
Chroma. Diese Evaluation ist ausschließlich dokumentarisch. Es wurden keine
Pakete installiert, Modelle geladen, Dienste gestartet oder Netzwerkzugriffe aus
Sagent ausgeführt.

## Verbindliche Kriterien

1. Local-first ohne Cloudkonto oder Remote-Endpunkt.
2. In-Process-/Embedded-Betrieb für Tests und kleine persönliche Datenmengen.
3. Expliziter lokaler Persistenzpfad; keine versteckte Default-Persistenz.
4. Metadatenfilter für `kind`, `source`, `status` und `project_id`.
5. Vom Embedder getrennte Speicherung; Sagent behält die Kontrolle über Modellwahl.
6. Deterministische Offline-Tests ohne laufenden Provider.
7. Späterer Wechsel zu einem lokalen Server ohne Änderung des Memory-Domänenvertrags.
8. Kein automatischer Download, keine Telemetrieannahme und kein Cloud-Fallback.

## Offiziell dokumentierte Eigenschaften

| Kriterium | Qdrant | Chroma |
| --- | --- | --- |
| Embedded/In-Memory | Python Local Mode unterstützt In-Memory | Python `EphemeralClient` unterstützt In-Memory |
| Lokale Persistenz | Local Mode kann auf einen Pfad persistieren | `PersistentClient(path=...)` persistiert lokal |
| Metadatenfilter | Payload-Filter sind Teil der Query-API | Collections unterstützen Metadatenfilter |
| Separater Server | Optional; Local Mode benötigt keinen Server | Optional; Python kann embedded laufen |
| Späterer Serverbetrieb | Client kann auf lokalen Qdrant-Server zeigen | `HttpClient` kann auf lokalen Chroma-Server zeigen |

Quellen:

- [Qdrant Local Quickstart](https://qdrant.tech/documentation/quick-start/)
- [Qdrant Local Mode](https://qdrant.tech/documentation/frameworks/langchain/)
- [Chroma Clients](https://docs.trychroma.com/docs/run-chroma/clients)
- [Chroma Architecture](https://docs.trychroma.com/reference/architecture/overview)

## Entscheidung für den ersten Spike

Qdrant Local Mode ist der bevorzugte Kandidat für den ersten separaten
Implementierungs-Spike. Ausschlaggebend sind der explizite kleine Local-Mode-Scope,
In-Memory-/On-Disk-Betrieb und die dokumentierte Payload-Filterung, die direkt zu
Sagents festen Memory-Metadaten passt.

Chroma bleibt der Vergleichskandidat. Die Auswahl ist erst bestätigt, wenn ein
eigener Branch beide Adapter gegen denselben vollständig synthetischen Katalog
prüft. Bis dahin bleibt der aktuelle SQLite-/Token-Suchvertrag der aktive,
abhängigkeitsfreie Fallback.

Der dafür notwendige providerneutrale `VectorStore`-Vertrag und ein begrenzter
synthetischer In-Memory-Adapter sind bereits implementiert. Damit kann der spätere
Vergleich denselben Upsert-/Query-/Filter-/Delete-Vertrag verwenden, ohne API oder
Memory-Domänenmodell erneut zu ändern.

## Pflichtprüfungen vor einer Abhängigkeit

- Lockfile-gebundene Installation separat freigeben.
- Paketgröße, transitive Abhängigkeiten und macOS/Python-3.12-Kompatibilität prüfen.
- Telemetrie, Hintergrundthreads und Dateipfade explizit deaktivieren oder binden.
- Nur synthetische Texte und injizierte feste Vektoren verwenden.
- Kein Ollama-, Modell-, Cloud- oder Remote-HTTP-Kontakt im Adaptertest.
- Schreib-, Lösch- und Reset-Aktionen an bestehende Approval-Verträge binden.
- Datenmigration und vollständige lokale Löschung negativ testen.

## Noch nicht freigegeben

- `qdrant-client`, `chromadb` oder Embedding-Pakete installieren,
- einen Qdrant-/Chroma-Server oder Container starten,
- Modelle oder Collections automatisch laden,
- Memory automatisch in Prompts einfügen,
- Cloud-Synchronisierung oder Remote-Endpoints konfigurieren.
