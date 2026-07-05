# Architektur

> **Pflegebereich:** aktueller technischer Aufbau. Zukunftsplanung gehört in `ROADMAP.md`.

## Systembild

```text
Next.js Web
    |
    v
FastAPI Agent API
    |---- Plan/Approval/Code-Edit/Test/Git Basispfad
    |---- ModelRouter -> Fake oder fester Loopback-Adapter
    |---- ModelJobService + Streaming
    |---- MemoryService -> SQLite + Ollama Embeddings
    `---- experimenteller Agent Loop -> ToolRegistry
```

## Komponenten

### Web

`apps/web` enthält Chat, Konversationssidebar, Plan-/Approval-Ansichten, Model- und Memory-Panel, Capability-/Cloud-Previews, Code-Edit, Tests, Git und Tool-Events. Die UI ist kein Policy-Enforcer; sicherheitsrelevante Entscheidungen müssen serverseitig validiert werden.

### Agent API

`apps/agent-api` bindet lokal an `127.0.0.1` und stellt die HTTP-/SSE-Schnittstelle bereit. Derzeit liegen dort auch Agent-Loop-Adapter. Diese direkte Kopplung ist funktional, aber noch keine saubere Sicherheitsgrenze.

### Agent Core

`packages/agent-core` enthält unveränderliche Modellverträge, Routing, Jobs, ChangeSets, Capability- und Cloud-Policies sowie die ToolRegistry. Modellantworten bleiben `untrusted=true`.

### Tools

`packages/tools` enthält den geprüften `WorkspaceGuard`, `FileTool`, allowlist-basierten `TestRunner` und begrenzten `GitTool`. Die direkten MVP-4-Adapter in `apps/agent-api` sind davon getrennt und teilweise weniger streng.

### Memory

`packages/memory` speichert Einträge in SQLite. Embeddings werden lokal über Ollamas `nomic-embed-text` erzeugt; die Ähnlichkeitssuche verwendet Cosine Similarity in Python. Memory ist Kontext, keine Autorität.

## Modellfluss

- Standardroute: deterministischer In-Process-Fake
- lokale Route: fest konfiguriertes LM-Studio- oder Ollama-Profil auf `127.0.0.1`
- Ausgabe: Text, Usage, Adapteridentität und `untrusted=true`
- Jobfluss: `queued → running → succeeded|failed` oder `cancelling → cancelled`
- Streaming: direkte Completion und Agent Loop über SSE
- Cloud: keine Runtime, `remote_http` blockiert

## Zwei Kontrollpfade

### Geprüfter Basispfad

`intake → plan → preview → approve → apply → verify`

ChangeSets, Hash-Bindung, Test-Allowlist und Git-Grenzen werden serverseitig geprüft.

### Experimenteller Agent Loop

`model response → parse TOOL_CALL → registry dispatch → TOOL_RESULT → next model call`

Dieser Pfad ist leistungsfähiger, aber noch nicht gleichwertig abgesichert. Verbindliche Risiken stehen in [`security/AGENT_LOOP.md`](security/AGENT_LOOP.md).

## Persistenz

- Memory: SQLite unter lokalem Sagent-State
- ModelJobs, Plan-/Approval- und ChangeSet-Zustände: prozesslokal
- Chat-/UI-Zustand: teilweise Frontend-State
- Cloud: keine Persistenz und keine Ausführung

Persistenzdetails werden in den jeweiligen Subsystemdokumenten gepflegt, nicht hier dupliziert.
