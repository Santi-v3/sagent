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

Die lokale API bietet ausschließlich einen prozesslokalen Store-Flow über
`POST /memory/entries/preview`, `/approve` und `/apply`. Approval und Apply sind an
Proposal-ID und exakten SHA-256-Hash gebunden; Apply verlangt zusätzlich
`confirmed=true` und ist nicht wiederholbar. Es existiert noch keine Web-UI, keine
Search-/Delete-Route, keine automatische Prompt-Anreicherung und kein implizites
Speichern aus Chats oder Modellantworten.
