# Handoff

> **Pflegebereich:** aktueller Checkout- und Übergabestatus. Ausführliche Historie: [`history/HANDOFF_THROUGH_2026-07-03.md`](history/HANDOFF_THROUGH_2026-07-03.md).

## Stand

- Datum: 2026-07-04
- Branch: `feat/agent-loop-memory-tools`
- Basis: lokales `main` bei PR #26
- Fokus: Dokumentationskonsolidierung und Agent-Loop-Härtung

## Implementiert

- MVP 1: Plan, Approval, ChangeSets, TestRunner und begrenztes Git
- MVP 2: lokale Modellprofile, Jobs, Cancel, Streaming und UI-Modellwahl
- MVP 3: SQLite-Memory, Ollama-Embeddings, Suche und UI
- MVP 4: Agent Loop, SSE-Streaming, Conversation-Kontext, Memory-Injektion und 16 Tools
- Cloud: ausschließlich deaktivierte Offline-Verträge und Preview-Metadaten

## Verifikation

- `pnpm check`: bestanden
- `pnpm build`: bestanden
- `uv run pytest -q`: 338 Python-Tests bestanden
- Webtests: 47 bestanden

## Nicht commitierter Zustand

- bestehende Sidebar-Änderung in `apps/web/components/sagent-shell.tsx`
- Test-/Provenienz- und Dokumentationsbereinigungen
- lokaler Starter `start.command`

Vor Commit muss der vollständige aktuelle `git diff` erneut geprüft werden. Diese Datei dokumentiert keinen Push und keinen Pull Request.

## Wichtigste Risiken

- Agent-Loop-Shell verwendet `shell=True` ohne echte OS-Sandbox.
- direkte Schreibadapter erzwingen den `WorkspaceGuard` nicht durchgängig.
- `code_edit_apply` kann im Agent Loop intern freigeben und anwenden.
- Tool-Aufrufe werden aus untrusted Modelltext erkannt und direkt dispatcht.

## Nächster sinnvoller Schritt

Die P0-Aufgaben aus [`TASKS.md`](TASKS.md) bearbeiten, beginnend mit Workspace-Grenzen und externer Approval-Bindung. Keine zusätzlichen Agent-Rechte hinzufügen.
