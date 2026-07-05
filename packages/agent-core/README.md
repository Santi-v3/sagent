# Agent Core

> **Pflegebereich:** Verträge und Policy-Bausteine in `packages/agent-core`. Systemstatus steht in `docs/ARCHITECTURE.md`.

Enthalten sind:

- ChangeSets, Proposal-Hashes und Approval-/Apply-Lebenszyklus
- provider-neutrale Modell-Requests und -Responses
- Herkunftslabels für Policy, Nutzer, Workspace, Memory und Tool-Ergebnisse
- deterministischer Fake-Adapter und fester Loopback-Adapter
- ModelRouter, Transport-Allowlist, Limits und Response-Validierung
- Cancellation und begrenzte ModelJobs
- Benchmark-Harness mit synthetischen Aufgaben
- Capability-Policy und deaktivierte Cloud-Verträge
- ToolRegistry für registrierte Agent-Werkzeuge

Modellantworten bleiben unveränderlich `untrusted=true`. Der Modelladapter erhält keine Tool-Definitionen. Die spätere Interpretation von Text als `TOOL_CALL` findet im Agent-API-Paket statt und ist eine separate Risikogrenze.

## Tests

```bash
uv run pytest packages/agent-core/tests
uv run ruff check packages/agent-core
```
