# Web App

> **Pflegebereich:** sichtbare UI-Funktionen und lokaler Start. Fortschritt gehört in `docs/ROADMAP.md`.

Die Next.js-Oberfläche bietet:

- Chat mit Conversation-Verlauf, Sidebar, Suche und Projekten
- lokale Modellantworten und SSE-Streaming
- sichtbare Agent-Tool-Calls
- Plan-, Risiko- und Approval-Ansichten
- Model- und Memory-Panel
- Code-Edit Preview, Approval und Apply
- Test- und Git-Ansichten
- Capability-, Benchmark- und deaktivierte Cloud-Previews

Git-Commit, Push, Merge und Cloud-Ausführung werden nicht angeboten. Tool-Chips zeigen Agent-Aktivität, ersetzen aber kein Sicherheits-Approval.

## Start

```bash
pnpm --filter @sagent/web dev
```

Danach läuft die Oberfläche unter `http://127.0.0.1:3000`.
