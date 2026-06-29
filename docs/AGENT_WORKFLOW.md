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

- Nur angezeigte und erlaubte Checks ausführen
- Exit-Codes und begrenzte Ausgaben erfassen
- Finalen Diff und unerwartete Änderungen prüfen
- Bei Fehlern keine zusätzlichen Reparaturen ohne neuen Vorschlag durchführen

## 8. Report und Handoff

- Ergebnis, Tests, verbleibende Risiken und nächste Schritte zusammenfassen
- Audit-Log abschließen
- Nur freigegebene, langfristig relevante Fakten ins Memory schreiben
- `docs/HANDOFF.md` aktualisieren, wenn die Arbeit über Sessions fortgesetzt wird
- Abgeschlossene Arbeit auf dem aktuellen Aufgaben-Branch committen
- Push, Merge und andere externe Git-Aktionen weiterhin separat freigeben

## Abbruchbedingungen

Der Agent stoppt bei Workspace-Ausbruch, fehlender Freigabe, verändertem Proposal, unerwarteten Dateien, Secret-Fund, nicht erlaubtem Befehl oder unklaren externen Auswirkungen.
