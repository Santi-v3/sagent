# Memory

Lokale, begrenzte Memory-Verträge für MVP 3. Der aktuelle Python-Service arbeitet
standardmäßig prozesslokal, verwendet eine deterministische Token-Suche und bindet
Mutationen an explizite Freigaben. Siehe [`docs/MEMORY.md`](../../docs/MEMORY.md)
und die [Vector-Store-Evaluation](../../docs/MEMORY_V2_VECTOR_STORE_EVALUATION.md).

Memory-Einträge sind transparent, bearbeitbar, löschbar und niemals höher
priorisiert als aktuelle Nutzeranweisungen oder Sicherheitsregeln. Vector Stores,
Embedding-Modelle, automatische Prompt-Anreicherung und Cloud-Synchronisierung sind
nicht aktiviert.

Der providerneutrale Vector-Store-Vertrag kann mit einem festen synthetischen
Katalog offline geprüft werden. Der Evaluator führt keine Modelle oder Provider aus
und enthält keine Netzwerk- oder Endpoint-Konfiguration.
