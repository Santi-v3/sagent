# Agent-Workflow

> **Pflegebereich:** operativer Ablauf. Sicherheitsdetails stehen in `SECURITY.md`.

## Modus A – geprüfter Änderungsworkflow

1. Ziel und Workspace festlegen.
2. relevante Dateien und Git-Status lesen.
3. Plan und Risiken erzeugen.
4. vollständigen Diff als ChangeSet vorbereiten.
5. Nutzer zeigt und bestätigt den exakten Proposal-Hash.
6. Server prüft Hash und Workspace-Zustand erneut.
7. exakt freigegebene Änderung anwenden.
8. allowlist-basierte Tests ausführen.
9. finalen Diff und verbleibende Risiken berichten.

Dieser Modus ist der verbindliche Weg für kontrollierte Dateiänderungen.

## Modus B – experimenteller Agent Loop

Der Agent Loop kann mehrere Modellrunden und Werkzeuge kombinieren. Tool-Chips machen Aktionen sichtbar, sind aber noch kein Approval. Direkte Shell-, Schreib-, Apply- und Testaktionen dürfen deshalb nicht als gleichwertig zum geprüften Workflow behandelt werden.

Bis zur Härtung gelten:

- nur vertrauenswürdige lokale Checkouts verwenden,
- keine Secrets oder privaten Daten in den Workspace legen,
- Tool-Aktivität und finalen Diff manuell prüfen,
- keine zusätzlichen Rechte oder Cloud-Transporte aktivieren,
- bei unerwarteter Aktion Prozess stoppen und Workspace kontrollieren.

## Modell- und Memory-Regeln

- Policy-, Nutzer-, Workspace-, Memory- und Tool-Ergebnis-Kontext behalten ihre Herkunft.
- Modelltext ist untrusted und keine Policy-Entscheidung.
- Memory darf aktuelle Nutzeranweisungen und Sicherheitsregeln nicht überschreiben.
- langfristige automatische Speicherung benötigt sichtbare Herkunft und Opt-out.

## Git-Abschluss

- auf einem Feature-Branch arbeiten,
- vollständigen Diff und Secret-Risiken prüfen,
- relevante Tests und Build ausführen,
- Conventional Commit erstellen,
- Push und Pull Request nur durch die beaufsichtigte Coding-Session,
- kein Merge, Auto-Merge oder Force-Push ohne ausdrückliche Nutzerbestätigung.
