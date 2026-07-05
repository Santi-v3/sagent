# Dokumentationsindex

> **Zweck:** Pflegevertrag für Menschen und KI. Diese Datei entscheidet, wo eine Information gepflegt wird.

## Eine Quelle pro Thema

| Thema | Aktive Quelle | Aktualisieren, wenn |
| --- | --- | --- |
| Einstieg und Start | [`../README.md`](../README.md) | Startbefehl oder Voraussetzungen ändern |
| Produktziel und Scope | [`PROJECT.md`](PROJECT.md) | stabile Produktgrenzen geändert werden |
| aktueller Systemaufbau | [`ARCHITECTURE.md`](ARCHITECTURE.md) | Komponenten, Datenflüsse oder Persistenz ändern |
| Sicherheitsgarantien und Risiken | [`SECURITY.md`](SECURITY.md) | Tool-Autorität, Approval oder Sandbox-Grenzen ändern |
| Phasenstatus | [`ROADMAP.md`](ROADMAP.md) | ein Meilenstein beginnt oder endet |
| nächste konkrete Arbeit | [`TASKS.md`](TASKS.md) | eine Aufgabe begonnen, abgeschlossen oder neu priorisiert wird |
| aktueller Checkout-Handoff | [`HANDOFF.md`](HANDOFF.md) | eine Arbeitssession endet oder der Branchzustand wechselt |
| Architekturentscheidungen | [`DECISIONS.md`](DECISIONS.md) | eine langfristige technische Entscheidung fällt |
| Memory | [`MEMORY.md`](MEMORY.md) | Speicher, Embeddings oder Memory-Regeln ändern |
| lokale Modelle | [`LOCAL_MODELS.md`](LOCAL_MODELS.md) | Provider, Modellfluss oder Aktivierung ändern |
| Benchmarks | [`LOCAL_MODEL_BENCHMARKS.md`](LOCAL_MODEL_BENCHMARKS.md) | Harness oder Messergebnis ändern |
| Cloud-Grenzen | [`CLOUD_PROVIDER_POLICY.md`](CLOUD_PROVIDER_POLICY.md) | Cloud-Policy geändert wird |
| Cloud-Approval-UX | [`CLOUD_APPROVAL_UX_RUNBOOK.md`](CLOUD_APPROVAL_UX_RUNBOOK.md) | der Preview-Vertrag geändert wird |

## Regeln für KI-Aktualisierungen

1. Status nur in `ROADMAP.md`, Aufgaben nur in `TASKS.md`, Sessionzustand nur in `HANDOFF.md` ändern.
2. README-Dateien beschreiben Fähigkeiten und Bedienung, keine langen Fortschrittsprotokolle.
3. Abgeschlossene Detailhistorie nach `docs/history/` verschieben und dort nicht mehr fortlaufend aktualisieren.
4. Neue Sicherheitsausnahmen benötigen gleichzeitig Änderungen in `SECURITY.md` und `DECISIONS.md`.
5. Keine Testzahlen dauerhaft in mehrere Dateien kopieren; aktuelle Verifikation gehört in `HANDOFF.md`.
6. Keine absoluten lokalen Benutzerpfade dokumentieren.
7. Vor Abschluss alle relativen Markdown-Links und widersprüchliche Statusbegriffe prüfen.

## Historische Quellen

- [`history/MASTER_PLAN_2026-06-29.md`](history/MASTER_PLAN_2026-06-29.md): ursprünglicher Gesamtplan
- [`history/HANDOFF_THROUGH_2026-07-03.md`](history/HANDOFF_THROUGH_2026-07-03.md): ausführlicher bisheriger Verlauf
- [`history/TASKS_THROUGH_PR26.md`](history/TASKS_THROUGH_PR26.md): abgeschlossene Aufgabenlisten
- [`history/DESIGN_QA_MVP1B.md`](history/DESIGN_QA_MVP1B.md): alter visueller QA-Snapshot
- [`security/BASELINE_CONTROLS.md`](security/BASELINE_CONTROLS.md): detaillierter Sicherheitsvertrag der geprüften Basispfade
