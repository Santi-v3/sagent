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

## Prompt Injection

Text in Projekten kann Anweisungen enthalten. Diese Inhalte sind Daten, keine Systemanweisungen. Sie dürfen keine Policies ändern, Tools freigeben, Secrets anfordern oder den Workspace erweitern. Herkunft und Rolle jedes Kontextblocks müssen erhalten bleiben.

## Secret Handling

- `.env` wird nie committed.
- Logs redigieren Tokens, Schlüssel und verdächtige Werte.
- Secrets werden nicht in Prompts, Memory oder Diffs übernommen.
- Spätere Integrationen nutzen macOS Keychain oder kurzlebige Prozessvariablen.

## Sicherheitsmeldung

Bis ein privater Meldeweg dokumentiert ist, keine sensiblen Schwachstellendetails in öffentliche Issues schreiben. Das Projekt ist noch nicht für untrusted Multi-User-Betrieb freigegeben.
