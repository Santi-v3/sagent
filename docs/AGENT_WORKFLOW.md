# Developer-Agent-Workflow

Der Workflow trennt Verstehen, Vorschlagen und Verändern. Kein Modell und kein Tool darf diese Grenzen überspringen.

## 1. Intake

- Ziel und gewünschtes Ergebnis erfassen
- Workspace und erlaubten Umfang festlegen
- Unklare oder risikoreiche Annahmen sichtbar machen
- Abbruch- und Erfolgskriterien definieren

## 2. Inspect

- Nur relevante, erlaubte Dateien lesen
- Repository-Status, Konventionen und vorhandene Tests prüfen
- Keine Änderungen und keine ausführenden Befehle
- Gelesene Quellen im Sitzungsprotokoll festhalten

## 3. Plan

- Kleine, überprüfbare Schritte formulieren
- Betroffene Dateien und erwartete Auswirkungen nennen
- Test- und Rückfallstrategie festlegen
- Sicherheitsklasse jeder geplanten Aktion bestimmen
- Falls ein Modell beteiligt ist, Kontextteile mit ihrer Herkunft (`policy`, `user`, `workspace`, `memory`, `tool_result`) kennzeichnen
- Modelltext ausschließlich als untrusted Entwurf behandeln; der deterministische Core entscheidet weiterhin über Policy, Approval und Tool-Aufrufe
- Standardmäßig den In-Process-Fake verwenden. Einen lokalen Adapter nur nach expliziter Loopback-Prozesskonfiguration, sichtbarer Adapterwahl und `confirmed=true` aufrufen
- Lokale Modellantworten wie jeden anderen Modelltext als untrusted Entwurf behandeln; sie dürfen niemals selbst Tools oder Approvals auslösen
- Längere Modellaufrufe als begrenzten Job starten, Job-ID sichtbar halten und dem Nutzer Status sowie aktiven Abbruch anbieten
- Nach Cancel erst `cancelled` als terminalen Zustand behandeln; `cancelling` autorisiert keine weiteren Aktionen

## 4. Propose

- Änderungen in einer isolierten Kopie vorbereiten
- Vollständigen Diff erzeugen
- Risiken, offene Annahmen und erwartete Prüfbefehle anzeigen
- Proposal hashen und unveränderlich machen

## 5. Approve oder Reject

- Mensch prüft Plan und Diff
- Ablehnung beendet oder überarbeitet den Vorschlag ohne Workspace-Änderung
- Freigabe ist an Proposal, Workspace und konkrete Aktionen gebunden
- Jede Änderung am Vorschlag macht eine neue Freigabe nötig

## 6. Apply

- Freigabe serverseitig erneut validieren
- Workspace-Zustand gegen erwarteten Ausgangszustand prüfen
- Exakt den freigegebenen Patch anwenden
- Bei Konflikt stoppen, nicht improvisieren

## 7. Verify

- Nur ein serverseitig registriertes, sichtbar ausgewähltes Testprofil ausführen
- Freigegebenen Task und exakten Anzeigebefehl serverseitig erneut prüfen
- Exit-Codes sowie begrenzte und redigierte Ausgaben erfassen
- Timeout oder unbekanntes Profil beendet den Verify-Schritt ohne improvisierten Ersatzbefehl
- Finalen Diff und unerwartete Änderungen prüfen
- Bei Fehlern keine zusätzlichen Reparaturen ohne neuen Vorschlag durchführen

## 8. Git Review

- Repository-Root, Branch und Worktree-Status über den begrenzten `GitTool` erfassen
- Auf `main`, `master`, `trunk` oder Detached HEAD keine Commit-Vorbereitung zulassen
- Falls nötig nur nach sichtbarer Bestätigung einen policy-konformen lokalen Feature-Branch erstellen
- Staged, unstaged und unversionierte Änderungen als begrenzten, Secret-redigierten Diff anzeigen
- Commit-Metadaten nur für den unveränderten, vollständigen und nicht redigierten Diff vorbereiten; dabei weder stagen noch committen
- Push und Merge im Sagent-Tool blockieren, bis dafür ein separater Approval-Flow implementiert und freigegeben ist

## 9. Report und Handoff

- Ergebnis, Tests, verbleibende Risiken und nächste Schritte zusammenfassen
- Audit-Log abschließen
- Nur freigegebene, langfristig relevante Fakten ins Memory schreiben
- `docs/HANDOFF.md` aktualisieren, wenn die Arbeit über Sessions fortgesetzt wird

## 10. Verbindlicher Git-Abschluss für die Coding-Session

Dieser Repository-Abschluss wird derzeit durch die beaufsichtigte Coding-Session ausgeführt, nicht durch den eingebauten Sagent-`GitTool`. Jede abgeschlossene Aufgabe folgt exakt diesem Ablauf:

1. Codex arbeitet auf einem Feature-Branch, niemals direkt auf `main`.
2. Codex führt die relevanten Tests, Linter, Typprüfungen und Builds aus.
3. Codex committet den geprüften Stand auf dem Feature-Branch.
4. Codex pusht den Feature-Branch zu GitHub.
5. Codex erstellt einen Pull Request gegen `main` oder liefert den PR-Link und eine klare Anleitung, falls die automatische Erstellung blockiert ist.
6. Der Nutzer prüft Diff, Testergebnisse und Risiken.
7. Der Merge erfolgt ausschließlich nach ausdrücklicher Bestätigung des Nutzers.

Ein neuer Commit nach der Prüfung macht eine erneute Prüfung erforderlich. Codex aktiviert kein Auto-Merge und merged niemals eigenständig.

### Vor jedem Commit

1. `git status` ausführen und den vollständigen Änderungsumfang prüfen.
2. Sicherstellen, dass ausschließlich Dateien der aktuellen Aufgabe enthalten sind.
3. Auf `.env`-Dateien, Secrets, API-Keys, Tokens, private Schlüssel und personenbezogene oder private Daten prüfen.
4. Relevante Tests, Linter, Typprüfungen und Builds erfolgreich abschließen.
5. Diff auf unerwartete, generierte oder binäre Dateien prüfen.

Wenn eine dieser Prüfungen fehlschlägt, wird nicht committed oder gepusht.

### Commit-Regel

Jede abgeschlossene Aufgabe endet mit einem sauberen Conventional Commit. Die Message beschreibt Zweck und Art der Änderung, zum Beispiel:

- `chore: initialize project structure`
- `feat: add agent task endpoint`
- `docs: update handoff`
- `test: add approval flow tests`
- `fix: block unsafe file paths`

### Branch-Regel

- Neue Features und Dokumentationsaufgaben erhalten einen verständlichen Feature-Branch.
- Empfohlene Namen sind beispielsweise `feature/developer-workflow-simulation`, `feature/workspace-guard`, `feature/test-runner` oder `docs/update-agent-workflow`.
- `main` ist der stabile Hauptbranch.
- Direkte Arbeit auf `main` ist nur beim initialen Projekt-Setup oder nach ausdrücklicher Nutzerfreigabe erlaubt.

### Push- und Pull-Request-Regel

- Nach erfolgreichem Commit darf ausschließlich der aktuelle Feature-Branch gepusht werden.
- Force-Push sowie Pushes von Secrets oder privaten Dateien sind verboten.
- Nach dem Push wird, wenn möglich, ein Pull Request gegen `main` erstellt.
- Wenn die automatische PR-Erstellung blockiert ist, nennt Codex den PR-Link oder die notwendigen Schritte.
- Der PR enthält eine kurze Zusammenfassung, Testergebnisse und bekannte Risiken.
- Fehlgeschlagene Tests blockieren den Merge.

### Pflichtbericht zum Aufgabenabschluss

Codex berichtet am Ende jeder Aufgabe:

- aktuellen Branch
- Commit-Hash und Commit-Message
- Push-Status
- PR-Status und PR-Link
- Testergebnis
- geänderte Dateien
- offene Risiken oder TODOs
- ob der Worktree sauber ist

## Abbruchbedingungen

Der Agent stoppt bei Workspace-Ausbruch, fehlender Freigabe, verändertem Proposal, unerwarteten Dateien, Secret-Fund, nicht erlaubtem Befehl oder unklaren externen Auswirkungen.
