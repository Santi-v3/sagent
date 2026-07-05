# Sicherheitsstatus

> **Pflegebereich:** tatsächlich erzwungene Garantien, bekannte Ausnahmen und offene Risiken. Historische Detailverträge der Basispfade: [`security/BASELINE_CONTROLS.md`](security/BASELINE_CONTROLS.md).

## Vertrauensmodell

Nutzertext, Repository-Inhalte, Memory und Modellantworten gelten als untrusted. Cloud-Transport ist deaktiviert. Lokale Modellaufrufe sind nur über feste Loopback-Profile vorgesehen.

## Geprüfter Basispfad

Der klassische Plan-/Proposal-/Approval-Pfad erzwingt:

- kanonische Workspace-Grenzen und Schutz sensibler Pfade
- inhaltsgebundene ChangeSets mit sichtbarem Diff
- getrennte Preview-, Approval- und Apply-Schritte
- allowlist-basierte Tests mit `shell=False`
- begrenzte Git-Inspektion und lokale Branch-Erstellung
- keine Commit-, Push- oder Merge-Aktion
- blockiertes `remote_http`

## Experimenteller Agent Loop

`POST /agent/execute` und `POST /agent/execute/stream` registrieren zusätzlich 16 Werkzeuge. Der Agent Loop ist funktional, erfüllt aber die Garantien des Basispfads noch nicht vollständig.

Aktuelle Risiken:

1. `bash` und `grep` verwenden `shell=True`.
2. Es gibt keine echte macOS-Dateisystem- oder Netzwerksandbox.
3. `write_file` und `edit_file` prüfen Pfade nicht durchgängig über `WorkspaceGuard`.
4. `code_edit_apply` führt Approval und Apply intern nacheinander aus.
5. Test- und Memory-Aktionen können ohne separate sichtbare Nutzerfreigabe dispatcht werden.
6. Tool-Aufrufe werden aus untrusted Modelltext geparst und direkt ausgeführt.

Folge: Nur in bewusst ausgewählten, vertrauenswürdigen lokalen Checkouts verwenden. Der Agent Loop ist keine Sicherheitsgrenze.

Ausführliche Analyse und Härtungsplan: [`security/AGENT_LOOP.md`](security/AGENT_LOOP.md).

## Cloud

- `remote_http` bleibt blockiert.
- Es gibt keinen automatischen Local-to-Cloud-Fallback.
- Cloud-Preview-Endpunkte aktivieren keinen Provider und laden keine Secrets.
- Jede spätere Cloud-Implementierung benötigt ein eigenes Threat Model und eine neue Entscheidung.

## Änderungsregel

Jede Änderung an Tool-Autorität, Approval, Workspace-Grenzen, Netzwerk oder Persistenz muss gleichzeitig aktualisieren:

- dieses Dokument,
- [`DECISIONS.md`](DECISIONS.md),
- relevante negative Tests,
- [`TASKS.md`](TASKS.md) beziehungsweise [`ROADMAP.md`](ROADMAP.md).
