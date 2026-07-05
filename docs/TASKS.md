# Aufgaben

> **Pflegebereich:** nur aktuelle und unmittelbar nächste Arbeit. Abgeschlossene Detailhistorie: [`history/TASKS_THROUGH_PR26.md`](history/TASKS_THROUGH_PR26.md).

## P0 – Agent Loop absichern

- [ ] freie Shell durch feste Befehlsprofile oder eine echte OS-Sandbox ersetzen
- [ ] `write_file` und `edit_file` vollständig über `WorkspaceGuard` und ChangeSets führen
- [ ] `code_edit_apply` von der internen Selbstfreigabe trennen
- [ ] Testausführung im Agent Loop an sichtbare externe Approval-Tokens binden
- [ ] Traversal-, Symlink-, Netzwerk-, Secret- und Approval-Bypass-Tests ergänzen
- [ ] Tool-Calls aus Modelltext als Vorschlag behandeln, nicht direkt als Autorisierung

## P1 – Dokumentation und Architektur

- [x] aktive Dokumentation entduplizieren und historische Snapshots auslagern
- [ ] Agent-Loop-Toolgrenze nach der Härtung als eigenes ADR aktualisieren
- [ ] aktuellen MVP-4-UI-Stand visuell prüfen und als QA-Snapshot archivieren

## P1 – Memory

- [ ] automatische Speicherung von Agent-Entscheidungen definieren
- [ ] sichtbare Herkunft, Löschung und Opt-out für automatisch gespeicherte Einträge ergänzen
- [ ] Fehlerverhalten dokumentieren, wenn Ollama-Embeddings nicht erreichbar sind

## P2 – Lokale Modelle

- [ ] LM Studio nur bei Bedarf gegen Ollama vergleichen
- [ ] Benchmark ausschließlich nach erneuter expliziter Bestätigung wiederholen

## Weiterhin blockiert

- Cloud-Adapter und `remote_http`
- Git-Commit, Push und Merge durch Sagent
- automatische Downloads oder Paketinstallation
- weitere Agent-Rechte vor Abschluss der P0-Härtung
