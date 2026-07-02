# Sicherheitsmodell

Sagent behandelt Sicherheit als Kernfunktion. Modellantworten, Repository-Inhalte, Memory und UI-Eingaben gelten immer als potenziell fehlerhaft oder bösartig.

## Unverhandelbare Regeln

1. **Workspace-Grenze:** Tools dürfen nur innerhalb eines explizit gewählten und kanonisch aufgelösten Workspace arbeiten.
2. **Read-only by default:** Neue Tools haben zunächst ausschließlich Leserechte.
3. **Explizites Approval:** Schreiben, Löschen, Umbenennen, Prozessstart und Netzwerkzugriff benötigen eine konkrete Freigabe.
4. **Proposal-Bindung:** Eine Freigabe gilt nur für den angezeigten Proposal-Hash, nicht für ähnliche oder später veränderte Aktionen.
5. **Keine freie Shell:** Kommandos werden als Argumentlisten aus einer Allowlist gestartet, nie über `shell=True` oder interpolierte Shell-Strings.
6. **Pfadvalidierung:** Absolute Pfade, Traversal und Symlink-Ausbrüche werden abgewiesen.
7. **Minimale Daten:** Secrets, `.env`-Inhalte, Schlüssel und bekannte Credential-Pfade werden weder gelesen noch geloggt.
8. **Ressourcenlimits:** Datei-, Output-, Prozesszeit- und Speicherlimits verhindern unkontrollierte Arbeit.
9. **Kein Netzwerk per Default:** Netzwerkzugriff ist in Tools standardmäßig deaktiviert.
10. **Auditierbarkeit:** Tool-Anfrage, Policy-Entscheidung, Approval und Ergebnis werden lokal und redigiert protokolliert.

## Approval-Stufen

- **Stufe 0 – Lesen:** Erlaubte Textdateien innerhalb des Workspace; bekannte sensible Pfade bleiben gesperrt.
- **Stufe 1 – Vorschlagen:** Pläne und Patches in einem isolierten Bereich erzeugen; keine Workspace-Mutation.
- **Stufe 2 – Ändern:** Exakt angezeigten Patch nach expliziter Freigabe anwenden.
- **Stufe 3 – Ausführen:** Einen angezeigten, allowlist-basierten Befehl mit Limits starten.
- **Stufe 4 – Extern:** Netzwerk, Paketveröffentlichung oder andere externe Effekte benötigen eine separate, besonders deutliche Freigabe. Für den definierten Git-Abschluss besteht eine dauerhafte, eng begrenzte Freigabe zum Push des aktuellen Feature-Branches und zur PR-Erstellung gegen `main`. Merge, Auto-Merge, Force-Push und Push auf `main` bleiben ohne ausdrückliche Bestätigung verboten.

## Git-Schutz

- Änderungen erfolgen ausschließlich auf einem Feature-Branch.
- `git status` und der vollständige Diff werden vor jedem Commit geprüft.
- Vor dem Commit wird auf Secrets, API-Keys, Tokens, `.env`-Dateien, private Schlüssel sowie personenbezogene oder private Daten geprüft.
- Vor dem Commit müssen die relevanten Tests, Linter, Typprüfungen und Builds erfolgreich sein.
- Commits folgen dem Conventional-Commit-Format und enthalten nur Änderungen der aktuellen Aufgabe.
- Nach dem Commit wird nur der aktuelle Feature-Branch gepusht.
- Pushes mit Secrets, privaten Dateien oder ungeprüften Änderungen sind verboten.
- Der Pull Request zeigt Zusammenfassung, Diff, Testergebnisse und bekannte Risiken.
- Ein Merge nach `main` erfolgt nur nach ausdrücklicher Nutzerbestätigung.
- Fehlgeschlagene Tests blockieren den Merge.
- Auto-Merge, Force-Push und direkte Arbeit oder Pushes auf `main` sind nicht Teil der dauerhaften Freigabe. Ausnahmen gelten nur für das initiale Projekt-Setup oder nach ausdrücklicher Nutzerfreigabe.

## Sandbox-Anforderungen

- Kanonischer Workspace-Root wird beim Sitzungsstart fixiert.
- Schreiboperationen laufen zunächst gegen eine temporäre Kopie oder einen Git-Worktree.
- Tools erhalten nur die benötigten Verzeichnisse und Umgebungsvariablen.
- Prozesse laufen mit festem Arbeitsverzeichnis, bereinigter Umgebung und Timeout.
- Änderungen werden vor Übernahme erneut gegen den freigegebenen Hash geprüft.

## Implementierter Datei-Sicherheitsvertrag (MVP 1.C)

- Der Workspace-Root wird einmal kanonisch aufgelöst und muss ein existierendes Verzeichnis sein.
- Tool-Eingaben akzeptieren ausschließlich relative Pfade. Absolute Pfade, jedes `..`-Segment und Symlink-Ziele außerhalb des Workspace werden abgewiesen.
- `.env`-Varianten, `.ssh`, bekannte SSH-Schlüssel, Token-/Secret-/Credential-Namen sowie private Schlüssel- und Zertifikat-Dateiendungen bleiben auch für Lese- und List-Operationen gesperrt.
- `FileTool` verarbeitet nur reguläre UTF-8-Textdateien ohne NUL-Bytes. Standardmäßig gelten 1 MiB pro Datei und 1.000 Einträge pro Listing.
- Erstellen setzt ein vorhandenes Elternverzeichnis voraus. Löschen, Umbenennen und automatisches Erstellen von Verzeichnissen sind nicht implementiert.
- Ein ChangeSet speichert Operation, relativen Pfad, alten und neuen SHA-256-Wert, alte und neue Inhalte sowie den sichtbaren Unified Diff.
- Approval und Apply erwarten denselben Proposal-Hash. Vor dem Schreiben wird der Ausgangszustand erneut geprüft; Abweichungen stoppen mit Konflikt statt vorhandene Arbeit zu überschreiben.
- Einzelne Datei-Schreibvorgänge sind atomar. Ein ChangeSet wird höchstens einmal angewendet und Schreibmethoden akzeptieren nur intern signierte, zu Pfad, Operation und neuem Inhalt passende Nachweise.

Die ChangeSet-Zustände sind noch nicht persistent, und mehrere Dateien bilden noch keine globale Dateisystemtransaktion. Deshalb bleibt die API-/UI-Anbindung bis zu einem eigenen Review deaktiviert.

### Implementierter Safe Local Code Edit Loop (PR #21)

Der Safe Local Code Edit Loop erlaubt das Vorschlagen, Freigeben und Anwenden einer einzelnen Dateiänderung über einen strengen Proposal → Preview-Diff → Approval-Fingerprint → Apply-Vertrag:

- **Proposal (Preview):** `POST /agent/code-edits/preview` akzeptiert relativen Pfad und neuen Textinhalt. Die Route validiert den Pfad (keine Traversal, keine absoluten Pfade, keine Symlink-Flucht, keine Hidden-/Sensitiv-Dateien), liest den aktuellen Inhalt über `FileTool`, erstellt einen `ChangeSet` mit SHA-256-Hashes und Unified Diff, und gibt `proposal_hash`, `change_set_id` und `diff` zurück. **Es wird nichts geschrieben.**
- **Approval (Fingerprint):** `POST /agent/code-edits/approve` akzeptiert `change_set_id` und `proposal_hash`. Der Hash muss exakt mit dem gespeicherten Proposal übereinstimmen (`hmac.compare_digest`). Ein Mismatch wird mit HTTP 409 blockiert. **Der einmal verwendete Approval kann nicht für andere Änderungen wiederverwendet werden.**
- **Apply (Geprüfte Ausführung):** `POST /agent/code-edits/apply` akzeptiert `change_set_id`, `proposal_hash` und `confirmed=true`. Vor dem Schreiben wird der Workspace erneut gegen den `old_sha256` geprüft (Stale-Workspace-Erkennung). Bei Abweichung wird HTTP 409 gemeldet. Der ChangeSet wird **genau einmal** angewendet; ein zweiter Apply-Versuch schlägt fehl.
- **Keine Tool-Autorität:** Keine der drei Routen führt Shell-Kommandos, Git-Aktionen, Netzwerkaufrufe, Cloud-Provider-Calls oder Modellanfragen aus. Die Responses enthalten `shell_executed=false`, `git_executed=false`, `network_used=false` und `model_authority=false`.
- **`model_response` wird abgewiesen:** Wenn ein Request ein `model_response`-Feld enthält, wird er mit HTTP 422 abgelehnt. Modellantworten dürfen keine Tool-Autorität erhalten.
- **Sicherheitsgrenzen:**
  - Nur erlaubte Textdateien im Workspace (keine NUL-Bytes, nur UTF-8, ≤1 MiB)
  - Pfad-Traversal (`..`) und absolute Pfade werden blockiert
  - Symlink-Ziele außerhalb des Workspace werden blockiert (auch indirekt über Alias)
  - `.env`-Dateien, versteckte Dateien (`.*`), Dependency-Manifeste und Lockfiles sind blockiert
  - Secrets in altem oder neuem Content werden vor Verarbeitung erkannt und blockiert
  - Binärdateien werden ohne Content-Leakage blockiert
  - Fehlerantworten enthalten keine sensiblen Dateiinhalte

## Implementierter Test-Sicherheitsvertrag (MVP 1.D)

- Requests wählen nur eine registrierte Profil-ID; ausführbare Datei, Argumente und Arbeitsverzeichnis stammen vollständig aus der serverseitigen Allowlist.
- Der Task muss zuvor menschlich freigegeben sein. Zusätzlich müssen `confirmed=true` und der exakt angezeigte Befehl übermittelt werden; Abweichungen stoppen vor dem Prozessstart.
- Prozesse starten mit `shell=False`, geschlossenem stdin, eigener Prozessgruppe, fixiertem kanonischem Workspace und einer neu aufgebauten Umgebung ohne geerbte Secrets.
- Wall-Clock-Timeout und CPU-Limit beenden die gesamte Prozessgruppe. Core-Dumps und die Zahl offener Dateideskriptoren sind begrenzt.
- stdout und stderr werden vollständig entleert, aber je Stream nur bis 64 KiB gespeichert. Bekannte Token-, Secret-, Passwort-, API-Key- und Private-Key-Muster werden vor Speicherung redigiert.
- Höchstens 100 unveränderliche Ergebnisse bleiben im Prozessspeicher. Ein fehlgeschlagener Test ist ein strukturiertes Ergebnis und kein API-Fehler.
- Standard-Proxyvariablen zeigen auf einen lokalen Blackhole-Endpunkt; Paketinstallation gehört nicht zur Allowlist. Web-Lint startet das bereits installierte lokale ESLint direkt, nicht den Paketmanager.

Diese Maßnahmen verhindern freie Shell-Kommandos und begrenzen versehentliche Nebenwirkungen. Sie sind noch keine OS-Sandbox: absichtlicher Raw-Socket-Zugriff oder Dateizugriff durch bösartigen Repository-Testcode ist technisch weiterhin möglich. Solche Workspaces dürfen erst nach einer späteren macOS-Sandbox ausgeführt werden.

## Implementierter Git-Sicherheitsvertrag (MVP 1.E)

- `GitTool` akzeptiert genau einen kanonischen Workspace, der dem Git-Repository-Root entsprechen muss. Verschachtelte oder übergeordnete Repositories werden abgewiesen.
- Git wird über einen vertrauenswürdigen absoluten Executable-Pfad, feste interne Argumentlisten, `shell=False`, geschlossenes stdin, deaktivierte Prompts und eine neu aufgebaute Umgebung gestartet. Globale und System-Konfiguration, Hooks, Pager, externe Diff-Programme und Textconv bleiben deaktiviert.
- Read-only-Aufrufe setzen `GIT_OPTIONAL_LOCKS=0`. Laufzeit, stdout, stderr und die Zahl der Status-Einträge sind begrenzt; eine gesamte Prozessgruppe wird bei Timeout beendet.
- Statuspfade werden gegen die Workspace-Secret-Policy geprüft. Sensible Pfade erscheinen nur als `[sensitive path hidden]` und werden nicht an Diff-Befehle übergeben.
- Der Review-Diff umfasst staged, unstaged und unversionierte erlaubte Textdateien. Er ist größenbegrenzt, markiert Kürzungen und redigiert bekannte Token-, Secret-, Passwort-, API-Key- und Private-Key-Muster.
- Lokale Branch-Erstellung benötigt `confirmed=true`, den unveränderten angezeigten Ausgangsbranch und einen Namen mit `codex/`, `feature/`, `fix/`, `docs/`, `test/` oder `chore/`. Auf `main`, `master`, `trunk` und Detached HEAD wird sichtbar gewarnt.
- Die Commit-Vorbereitung ist rein deklarativ: Sie staged und committet nichts. Sie wird auf geschützten Branches sowie bei leerem, verändertem, gekürztem oder redigiertem Diff blockiert und akzeptiert nur eine einzelne Conventional-Commit-Betreffzeile.
- Push und Merge sind Methoden, die immer einen Policy-Fehler auslösen. API und UI besitzen keine entsprechenden Routen oder Aktionen. Force-Push und Auto-Merge sind ebenfalls nicht verfügbar.

Der MVP-Git-Vertrag ist noch kein vollständiger Commit-Approval-Flow: Es gibt weder Staging noch Commit-Ausführung. Die bestehende Codex-Session kann den geprüften Feature-Branch gemäß dem dokumentierten Repository-Workflow committen und pushen; der in Sagent eingebaute Agent darf das noch nicht.

## Implementierter Modell-Sicherheitsvertrag (MVP 2.A)

- Modellanfragen bestehen aus unveränderlichen Textteilen mit erhaltenem Herkunftslabel: `policy`, `user`, `workspace`, `memory` oder `tool_result`. Ein Label erweitert niemals Tool- oder Systemrechte.
- Der Adaptervertrag kann ausschließlich Text vervollständigen. Er kennt weder Tool-Router noch Datei-, Prozess-, Git-, Netzwerk- oder Approval-Methoden und besitzt keine Tool-Call-Struktur.
- Fähigkeiten (`chat`, `coding`) werden explizit auf registrierte Adapter geroutet. Unbekannte Adapter, fehlende Routen und Capability-Mismatches werden vor Ausführung blockiert.
- Transportarten sind Teil der Policy. Standardmäßig ist ausschließlich `in_process` erlaubt; `loopback_http` und `remote_http` werden vor Adapter-Ausführung abgewiesen. Zusätzlich bleiben selbst In-Process-Adapter mit `simulated=false` gesperrt, bis die Laufzeit sie ausdrücklich aktiviert.
- Zahl und Gesamtgröße der Eingabeteile sowie die Ausgabelänge sind begrenzt. Streaming ist im Fake nicht erlaubt. Request-ID, Adapter-ID und Modell-ID werden nach der Antwort erneut abgeglichen.
- Jede `ModelResponse` ist technisch unveränderlich `untrusted=true`. Modelltext wird nicht als Approval, Policy-Entscheidung oder ausführbare Aktion interpretiert.
- Der aktuelle `FakeModelAdapter` ist deterministisch und führt keinen Modell-, Netzwerk- oder Tool-Aufruf aus. Die API gibt weder Endpoint-Konfiguration noch Zugangsdaten zurück.
- Adapterfehler werden in eine generische Fehlermeldung übersetzt, damit Provider-Interna nicht über die API-Grenze austreten.

## Implementierter Loopback-Modellvertrag (MVP 2.B)

- Die Standardkonfiguration registriert weiterhin nur den Fake. Ein lokaler Adapter benötigt gleichzeitig `SAGENT_NETWORK_ENABLED=loopback`, ein festes Providerprofil, eine Base-URL und eine Modell-ID.
- LM Studio ist ausschließlich unter `127.0.0.1:1234`, Ollama ausschließlich unter `127.0.0.1:11434` erlaubt. Schema muss `http` und Pfad `/v1` sein. IPv6, `localhost`, DNS, alternative IP-Darstellungen, andere Ports, URL-Credentials, Query und Fragment werden abgewiesen.
- Der HTTP-Client nutzt `trust_env=false`, folgt keinen Redirects, aktiviert kein HTTP/2, sendet `Accept-Encoding: identity`, übernimmt keine Cookies oder Proxies und setzt keinen `Authorization`-Header.
- Der Request enthält ausschließlich `model`, source-labelled `messages`, `temperature`, `max_tokens` und `stream=false`. Tool-Definitionen, Tool-Choice und frei wählbare Endpoints sind nicht Teil des API-Requests.
- Connect-, Read-, Write- und Pool-Timeout sowie Request-/Response-Bytes sind begrenzt. Es gibt keine automatischen Retries.
- HTTP-Fehlertexte, Connection-Details und Timeout-Details verlassen den Adapter nicht. Redirects, falscher Content-Type, ungültiges UTF-8/JSON, falsche Modell-ID, mehrere Choices, Tool-/Function-Calls, unerlaubte Finish-Reasons und fehlerhafte Usage werden blockiert.
- `POST /models/complete` akzeptiert nur registrierte `loopback_http`-Adapter, begrenzten Text und `confirmed=true`. Die Antwort bleibt `untrusted=true` und `simulated=false`.
- Die Konfiguration wird beim ersten Routerbau im Prozess gecacht. Ein Request kann Provider, URL, Port oder Modell nicht austauschen.

## Implementierter Modell-Cancellation-Vertrag

- `ModelCancellationToken` setzt genau einmal ein thread-sicheres Signal und führt registrierte Resource-Close-Callbacks idempotent aus. Spät registrierte Ressourcen werden sofort geschlossen.
- Router, Fake und Loopback-Adapter prüfen Cancellation vor Dispatch und vor Rückgabe. Der Loopback-Adapter prüft zusätzlich während des Response-Streams.
- Ein aktiver Cancel schließt sowohl HTTP-Client als auch Response. Transportfehler infolge dieses Close werden als `ModelCancelledError`, nicht als Providerfehler, klassifiziert.
- `ModelJobService` ist auf 1–4 Worker und 1–1.000 Jobs konfigurierbar; die API nutzt einen Worker und maximal 100 Jobs. Sind alle Slots aktiv, wird kein weiterer Job angenommen.
- API-Snapshots enthalten Adapter, Capability, Zeitpunkte, Status und Ergebnis, aber weder Prompt noch vollständigen Request. Nach Terminalstatus wird der interne Request verworfen.
- Fehlertexte aus Adaptern werden im Jobstatus nicht übernommen. Jobs melden ausschließlich die generische Meldung `Local model job failed safely.`
- Jobstart benötigt weiterhin `confirmed=true` und einen vorkonfigurierten nicht simulierten Loopback-Adapter. Cancel ist nur für queued/running/cancelling Jobs erlaubt und für bereits cancelled Jobs idempotent.
- Beim API-Shutdown werden aktive Tokens gesetzt und der begrenzte Executor geschlossen. Jobzustände bleiben bewusst flüchtig.

Die technische Loopback- und Cancellation-Grenze ist implementiert und mit Mock-Transports sowie Parallelitäts-Races negativ getestet. Eine Live-Evaluation gegen tatsächlich gestartete LM-Studio-/Ollama-Server bleibt separat, damit Installation, Modellwahl und Ressourcenverbrauch nicht stillschweigend verändert werden.

## Benchmark-Sicherheitsvertrag (MVP 2.C-Grundstein)

- Die Benchmark-CLI baut ohne `--confirmed` keinen Router und führt keinen Netzwerkzugriff aus.
- Ein bestätigter Lauf benötigt zusätzlich die bestehende vollständige Loopback-Prozesskonfiguration. Nur `127.0.0.1:1234` für LM Studio oder `127.0.0.1:11434` für Ollama ist möglich; `remote_http` bleibt blockiert.
- Provider, Endpoint, Modell und Prompt sind keine CLI-Argumente. Die Aufgaben stammen aus einem kleinen, versionierten Katalog synthetischer Daten.
- Die Harness installiert oder startet keine Software und führt keine Modell-Downloads aus.
- Berichte enthalten keinen Prompt und keinen Modelltext. Sie speichern nur Task-ID, Terminalstatus, begrenzte Zeit-/Längenmetriken, Untrusted- und Cancellation-Flags sowie generische Fehlercodes.
- Modelltext bleibt untrusted und wird weder ausgeführt noch an Tools, Approval oder Policies weitergereicht.
- Tests verwenden ausschließlich Mock-Transports. Ein echter Benchmark ist ein separater, ausdrücklich bestätigter Nutzerschritt.

## Implementierter Code-Edit-Preview-Vertrag (MVP 2.D)

- `POST /agent/code-edits/preview` erzeugt einen deterministischen SHA-256-Hash aus Pfad, Inhalt und Änderungsbeschreibung. Die Antwort enthält einen Diff (read-only, nie ausgeführt) und deklariert `shell_executed=false`, `git_executed=false`, `network_used=false`, `model_authority=false`.
- `POST /agent/code-edits/approve` bindet die Freigabe an den exakten Proposal-Hash aus der Preview. Ein abweichender Hash oder ein bereits terminaler Status (approved/applied) wird mit 409 abgewiesen.
- `POST /agent/code-edits/apply` simuliert eine Anwendung (liest nie von der Festplatte und schreibt nie darauf). Erfordert vorherige Approval und denselben Proposal-Hash. Doppelte Applys werden mit 409 blockiert.
- Der Apply-Response enthält ebenfalls `shell_executed=false`, `git_executed=false`, `network_used=false`, `model_authority=false`.
- Alle drei Endpunkte akzeptieren ausschließlich POST mit `Content-Type: application/json`; der CORS-Allowlist-Eintrag begrenzt Ursprünge auf `localhost:3000` und `127.0.0.1:3000`.
- Die Webkomponente `CodeEditPreviewPanel` zeigt einen Read-Only-Badge und die Sicherheitsinvariante "Keine Shell · Kein Git · Kein Netzwerk · Kein Modell" an.
- Die Apply-Schaltfläche bleibt deaktiviert, bis eine erfolgreiche Approval vorliegt. Bei Pfad-/Inhaltsänderung nach der Preview wird der Vorschlag als "veraltet" markiert und alle Aktionsschaltflächen werden deaktiviert.
- Die UI enthält keine Commit-/Push-/Merge-/Shell-/Cloud-/DeepSeek-Schaltflächen, kein `model_response`-Eingabefeld und keine API-Key-/Secret-/Endpoint-Felder.

## Geplanter Cloud-Provider-Vertrag (nicht implementiert)

Die verbindlichen Konzeptgrenzen für spätere optionale Cloud-Modelle stehen in
[`CLOUD_PROVIDER_POLICY.md`](CLOUD_PROVIDER_POLICY.md). Dieses Dokument erteilt keine
Runtime- oder Netzwerkfreigabe:

- `remote_http` bleibt technisch blockiert; local-first bleibt der Standard.
- DeepSeek Cloud wäre ein eigener Provider-Typ und niemals ein Ollama-/LM-Studio-Profil
  oder automatischer Local-to-Cloud-Fallback.
- Eine spätere Nutzung benötigt lokale Umgebungs-/Prozesskonfiguration und zusätzlich
  eine laufgebundene Nutzerfreigabe für Provider, Modell, Zweck und exaktes
  Datenmanifest.
- Secrets dürfen niemals übertragen werden; private oder vertrauliche Daten werden
  nicht automatisch weitergeleitet.
- Cloud-Antworten bleiben untrusted, erhalten keine Tool-Autorität und durchlaufen für
  Coding-Änderungen weiterhin den lokalen Diff-, Test- und Approval-Flow.
- Vor einer Implementierung sind Threat Model, Datenschutz-, Secret-, Kosten- und
  negative Offline-Tests als eigenes Sicherheitsinkrement erforderlich.

### Lokales Cloud-Approval-Preview-Wiring

Die Web-UI darf die bestehende lokale Route `POST /cloud/approval-preview` ausschließlich
für read-only Metadaten verwenden. Dieses Wiring ist keine Cloud- oder
`remote_http`-Freigabe:

- Der Browser nutzt die bestehende lokale Agent-API-Basis und keinen Cloud-Endpoint.
- Der Request enthält nur feste Provider-/Purpose-Metadaten, `approved=false`,
  `explicit_confirmed=false` sowie leere Disclosure-Flags und `bytes_estimate=0`.
- Prompts, Modelltexte, Datei- oder Diff-Inhalte, Secrets, Tokens, Endpoints und
  Netzwerkparameter sind weder Request- noch UI-Felder.
- Die UI akzeptiert nur eine weiterhin denied Response mit ausgeschlossenen Secrets,
  blockiertem Repository-Dump und `is_valid=false`.
- Bei nicht erreichbarer API oder Vertragsabweichung bleibt ausschließlich die
  versionierte statische Offline-Vorschau sichtbar.
- Das Wiring besitzt keinen Startbutton, keine Modellwahl, keine Tool-Autorität und
  keinen Providerbau.

Der spätere Nutzerablauf, seine Pflichtanzeigen, Blocker, Fehlerfälle und
Offline-Testanforderungen sind im
[`CLOUD_APPROVAL_UX_RUNBOOK.md`](CLOUD_APPROVAL_UX_RUNBOOK.md) spezifiziert. Das
Runbook ist keine Runtime-, Netzwerk-, Provider- oder Datenfreigabe; bis zu einem
separaten Security-Inkrement bleibt die Preview denied und `remote_http` blockiert.

### Deaktiviertes Cloud-Config-Schema

`CloudProviderConfig` ist ausschließlich unveränderliche Core-Metadaten. Das Schema
akzeptiert nur bekannte Cloud-Provider-IDs, erzwingt `enabled=false`, klassifiziert
den Transport als weiterhin blockiertes `remote_http`, verlangt explizites
`one_run_only`-Approval und unterstützt keine Endpoint-Konfiguration. Es speichert
weder Secretwerte noch Referenznamen und liest keine Umgebung. Die zugehörige
Validierung erteilt keine Ausführungsautorität, baut keinen Provider und verändert
weder `cloud_providers_enabled` noch die Transport-Allowlist des Routers.

Die lokale Route `GET /cloud/config-preview` und ihre read-only UI-Abbildung dürfen
nur diese statischen Metadaten anzeigen. Die Response enthält keine Secret-, Env-,
Endpoint-, Host-, Port- oder URL-Werte. Die UI akzeptiert nur `enabled=false`,
`remote_http_allowed=false`, `execution_allowed=false` und fällt bei Fehlern oder
Vertragsabweichungen auf dieselbe versionierte disabled Offline-Vorschau zurück.

## Implementierter Capability-Policy-Vertrag (PR #24)

Die Capability Policy ist ein reiner Offline-Vertrag, der Sagent-Subprozessen später eine granulare, konfigurierbare Berechtigungssteuerung erlaubt. Sie ersetzt keine bestehenden Sicherheitsgates, sondern ergänzt sie um einen deklarativen Policy-Layer:

- **CapabilityName:** 12 benannte Fähigkeiten (`read_workspace`, `preview_file_edits`, `apply_single_file_edit`, `apply_multi_file_edit`, `run_tests`, `run_shell_command`, `git_status`, `git_commit`, `git_push`, `change_dependencies`, `use_local_model`, `use_cloud_model`).
- **CapabilityMode:** `disabled`, `preview_only`, `approval_required`, `allowed`.
- **CapabilityPolicy:** Frozen Dataclass mit Mode-Zuordnung und Validierung (unbekannte Capabilities/Modi werden abgewiesen).
- **evaluate_capability():** Reine Funktion ohne Seiteneffekte. Gibt `CapabilityDecision` zurück (`allowed`, `needs_approval`, `preview_only`, `denied`).
- **DEFAULT_CAPABILITY_POLICY:**
  - `read_workspace`: preview_only
  - `preview_file_edits`: allowed
  - `apply_single_file_edit`: approval_required
  - `apply_multi_file_edit`: approval_required
  - `run_tests`: approval_required
  - `run_shell_command`: approval_required
  - `git_status`: allowed
  - `git_commit`: approval_required
  - `git_push`: approval_required
  - `change_dependencies`: approval_required
  - `use_local_model`: approval_required
  - `use_cloud_model`: disabled
- **Keine Runtime-Aktivierung:** Der Vertrag baut keine Router, führt keine Provider aus, startet keine Shell, führt keine Git-Operationen durch und liest weder Secrets, Env-Variablen noch Endpoints.
- **Modellantworten erhalten keine Tool-Autorität:** `evaluate_capability` akzeptiert keine `model_response`-Eingabe und gibt keine ausführbaren Referenzen zurück.
- **Unbekannte Capabilities:** Standardmäßig `disabled`/`DENIED`.
- **41 Tests** decken Default-Policy-Inhalt, Entscheidungslogik, Approval-Gating, Preview-Flag, Frozen-Validierung, Fehleingaben, Seiteneffektfreiheit und Secret-/Env-/Endpoint-Freiheit ab.

### Read-only Preview API und UI (PR #25)

`GET /capabilities/preview` gibt die Policy als sichere, niemals aktivierte Metadaten-Response zurück:
- Enthält alle 12 Capabilities mit Mode- und Entscheidungs-Metadaten (requires_approval, preview_only, disabled).
- Safety-Flags sind immer `false`: `shell_executed`, `git_executed`, `network_used`, `cloud_used`, `model_called`, `runtime_activated`.
- `policy_version` ist ein statischer Literal-String.
- **Keine Runtime-Aktivierung:** Die Route führt keine Shell, kein Git, kein Netzwerk, keine Cloud, keine Modellaufrufe und keine Runtime aus.
- **Keine Secrets/Endpoints/Env-Werte:** Die Response enthält keine API-Keys, URLs, Hosts, Ports, Endpoints oder Umgebungsvariablen.
- **Keine Settings-Persistenz:** Die Route speichert nichts, schreibt keine Dateien und liest keine Konfiguration außerhalb des Code-Moduls.
- Die React-Komponente `CapabilityPolicyPreview` zeigt die Daten read-only an, ohne Toggle-, Enable- oder Run-Buttons, ohne API-Key/Eingabefelder und mit statischem JSON-Fallback bei API-Fehlern.
- 11 API-Tests und 18 UI-Sicherheitstests bestätigen die Safety-Grenzen.

### Approval-Gated Test Runner (PR #26)

`POST /agent/test-runs/preview` → `approve` → `run` implementiert die erste echte Power-User-Fähigkeit mit mehrstufiger Sicherheit:
- **Capability-Policy-Gate:** `evaluate_capability(RUN_TESTS)` in der Preview.
- **Feste Allowlist:** Nur 4 vordefinierte Kommandos (python-pytest-all, python-pytest-capability, python-pytest-preview, python-lint). Kein freier command string.
- **Keine Shell:** argv aus festen Tupeln; `subprocess.Popen(…, shell=False)`.
- **Hash-gebundene Freigabe:** Preview liefert SHA-256-Hash über `test_run_id:command_id:approval_token`. Approve und Run prüfen den Hash.
- **Kein Re-Run:** Completed-Runs sind nicht wiederholbar.
- **Kein gleichzeitiger Lauf:** `_RUN_EXECUTION_LOCK` blockiert parallele Ausführung.
- **Environment-Sanitisierung:** Proxy auf 127.0.0.1:9, Temp-Home, keine Netzwerk-Env-Variablen.
- **Output-Begrenzung:** max 20 KB stdout/stderr; Timeout 60–120s.
- **Keine Git/Network/Install-Kommandos** in der Allowlist.
- **Keine Secrets/Endpoints/Env** in Responses.
- 39 Tests decken Allowlist-Validierung, Preview, Approve, Execute, Safety, Capability Gate und Secret-Freiheit ab.

## Prompt Injection

Text in Projekten kann Anweisungen enthalten. Diese Inhalte sind Daten, keine Systemanweisungen. Sie dürfen keine Policies ändern, Tools freigeben, Secrets anfordern oder den Workspace erweitern. Herkunft und Rolle jedes Kontextblocks müssen erhalten bleiben.

## Secret Handling

- `.env` wird nie committed.
- Logs redigieren Tokens, Schlüssel und verdächtige Werte.
- Secrets werden nicht in Prompts, Memory oder Diffs übernommen.
- Spätere Integrationen nutzen macOS Keychain oder kurzlebige Prozessvariablen.

## Sicherheitsmeldung

Bis ein privater Meldeweg dokumentiert ist, keine sensiblen Schwachstellendetails in öffentliche Issues schreiben. Das Projekt ist noch nicht für untrusted Multi-User-Betrieb freigegeben.
