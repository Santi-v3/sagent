# Aufgaben

Diese Liste ist nach Ausführungsreihenfolge sortiert. Jede Aufgabe soll klein genug für einen überprüfbaren Pull Request bleiben.

## Als Nächstes

- [ ] Root-Tooling installieren und Lockfiles erzeugen (`pnpm`, `uv`)
- [ ] `packages/agent-core` als echtes Python-Paket mit `src/`-Layout anlegen
- [ ] Domänenmodelle für `Session`, `Plan`, `ToolCall`, `Proposal`, `Approval` und `AuditEvent` definieren
- [ ] Workspace-Policy mit kanonischer Pfadauflösung implementieren
- [ ] Sicherheitsfälle für `..`, absolute Pfade, Symlinks, Binärdateien und Größenlimits testen
- [ ] Read-only-Tools `list_files` und `read_text_file` implementieren
- [ ] Deterministischen Planner für Fixture-Aufgaben implementieren
- [ ] Append-only JSONL-Audit-Log mit Redaction bauen
- [ ] CI für ruff, pytest und spätere TypeScript-Prüfungen hinzufügen

## Danach

- [ ] Unified-Diff-Datentyp und Patch-Parser definieren
- [ ] Patch zunächst nur gegen eine temporäre Workspace-Kopie anwenden
- [ ] Approval-Modell und Proposal-Hash spezifizieren
- [ ] Allowlist-basierten Command Runner entwerfen
- [ ] FastAPI-App scaffolden, ausschließlich auf localhost
- [ ] Next.js-App mit Plan-/Diff-Ansicht scaffolden

## Definition of Done

Eine Aufgabe ist fertig, wenn:

- Akzeptanzkriterien oder Tests vorhanden sind,
- Sicherheitsauswirkungen geprüft wurden,
- Formatierung, Linting und Tests erfolgreich sind,
- neue Entscheidungen dokumentiert wurden,
- `docs/HANDOFF.md` bei relevantem Session-Fortschritt aktualisiert wurde,
- keine Secrets, generierten Artefakte oder persönlichen Daten eingecheckt wurden.
