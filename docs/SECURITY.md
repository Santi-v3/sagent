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
- LM Studio ist ausschließlich auf Port `1234`, Ollama ausschließlich auf Port `11434` erlaubt. Host muss das exakte Literal `127.0.0.1` oder `::1`, Schema `http` und Pfad `/v1` sein. `localhost`, DNS, alternative IP-Darstellungen, andere Ports, URL-Credentials, Query und Fragment werden abgewiesen.
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
- Jobstart benötigt weiterhin `confirmed=true` und einen vorkonfigurierten nicht simulierten Loopback-Adapter. Cancel ist nur für queued/running Jobs erlaubt und für bereits cancelled Jobs idempotent.
- Beim API-Shutdown werden aktive Tokens gesetzt und der begrenzte Executor geschlossen. Jobzustände bleiben bewusst flüchtig.

Die technische Loopback- und Cancellation-Grenze ist implementiert und mit Mock-Transports sowie Parallelitäts-Races negativ getestet. Eine Live-Evaluation gegen tatsächlich gestartete LM-Studio-/Ollama-Server bleibt separat, damit Installation, Modellwahl und Ressourcenverbrauch nicht stillschweigend verändert werden.

## Prompt Injection

Text in Projekten kann Anweisungen enthalten. Diese Inhalte sind Daten, keine Systemanweisungen. Sie dürfen keine Policies ändern, Tools freigeben, Secrets anfordern oder den Workspace erweitern. Herkunft und Rolle jedes Kontextblocks müssen erhalten bleiben.

## Secret Handling

- `.env` wird nie committed.
- Logs redigieren Tokens, Schlüssel und verdächtige Werte.
- Secrets werden nicht in Prompts, Memory oder Diffs übernommen.
- Spätere Integrationen nutzen macOS Keychain oder kurzlebige Prozessvariablen.

## Sicherheitsmeldung

Bis ein privater Meldeweg dokumentiert ist, keine sensiblen Schwachstellendetails in öffentliche Issues schreiben. Das Projekt ist noch nicht für untrusted Multi-User-Betrieb freigegeben.
