# Memory V1

## Zweck

Memory hilft Sagent, stabile Projektkonventionen, Entscheidungen und offene Arbeit über Sitzungen hinweg zu verstehen. Es ist kein versteckter Prompt und keine Autoritätsquelle.

## Format

Version 1 verwendet Markdown-Dateien mit kleinem Frontmatter-Block:

```markdown
---
id: decision-001
type: decision
created_at: 2026-06-29
updated_at: 2026-06-29
source: user-approved
status: active
---

Inhalt mit klarer Herkunft und Gültigkeit.
```

## Geplante Bereiche

- `memory/profile/`: stabile Nutzerpräferenzen, nur nach ausdrücklicher Zustimmung
- `memory/projects/<project>/`: Projektkontext und Konventionen
- `memory/sessions/`: kompakte, redigierte Session-Zusammenfassungen
- `memory/decisions/`: bestätigte langfristige Entscheidungen

## Regeln

- Memory-Schreibvorgänge benötigen eine sichtbare Freigabe.
- Sensible Daten, Secrets und vollständige Chat-Transkripte werden nicht gespeichert.
- Jeder Eintrag hat Herkunft, Zeitstempel und Status.
- Aktuelle Nutzeranweisungen und Sicherheitsregeln haben Vorrang.
- Veraltete oder widersprüchliche Einträge werden markiert, nicht still überschrieben.
- Nutzer können Inhalte lesen, bearbeiten und löschen.

## Noch nicht in V1

- Embeddings oder Vektordatenbank
- Automatisches Profiling
- Cloud-Synchronisierung
- Implizites Lernen aus jeder Aktion
- Unbegrenzte Aufbewahrung

## Offline-Grundlage für Memory V2

Der Python-Core enthält eine kleine, weiterhin deaktivierte Grundlage für spätere
strukturierte Suche:

- Standardmäßig bleiben Einträge ausschließlich im Prozessspeicher.
- Speicherung und Löschung verlangen `confirmed=true` auf Service-Ebene.
- SQLite-Persistenz entsteht nur bei explizit injiziertem lokalem Datenbankpfad.
- Embeddings entstehen nur über eine injizierte Funktion; das Memory-Paket enthält
  keinen HTTP-Client, liest keine Umgebungsvariablen und kontaktiert kein Modell.
- Ohne Embedder steht eine deterministische lokale Token-Überschneidungssuche bereit.
- Einträge und Metadaten sind begrenzt; zurückgegebene Einträge sind unveränderlich.
- Die festen Klassen `project_knowledge`, `decision`, `task_history` und `summary`
  können nach `kind`, `source` und `status` gefiltert werden.

Die lokale API bietet einen prozesslokalen Store-Flow über
`POST /memory/entries/preview`, `/approve` und `/apply`. Approval und Apply sind an
Proposal-ID und exakten SHA-256-Hash gebunden; Apply verlangt zusätzlich
`confirmed=true` und ist nicht wiederholbar. `GET /memory/entries` und
`POST /memory/search` lesen begrenzte, als untrusted markierte Einträge ohne
Seiteneffekt. Löschung folgt einem getrennten Preview-/Approve-/Apply-Vertrag und
ist ebenfalls hashgebunden, bestätigt und nur einmal nutzbar. Es existiert noch
keine Web-UI, keine automatische Prompt-Anreicherung und kein implizites Speichern
aus Chats oder Modellantworten.

Die Auswahlkriterien und die vorläufige Wahl von Qdrant Local Mode für einen
separaten synthetischen Spike stehen in
[`MEMORY_V2_VECTOR_STORE_EVALUATION.md`](MEMORY_V2_VECTOR_STORE_EVALUATION.md).
