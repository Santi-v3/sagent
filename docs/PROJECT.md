# Projektdefinition

> Strategische Quelle: [`MASTER_PLAN.md`](MASTER_PLAN.md). Dieses Dokument fasst den aktuell relevanten Produktscope kompakt zusammen.

## Vision

Sagent wird ein persönlicher, lokal laufender Entwicklungsagent für macOS. Er soll technische Arbeit verständlich vorbereiten und kontrolliert ausführen, ohne dem Menschen die letzte Entscheidung abzunehmen.

## Zielgruppe

Zunächst ist Sagent ein persönliches Werkzeug für den Eigentümer dieses Repositories. Spätere Mehrbenutzer-, Cloud- oder Team-Funktionen sind kein Bestandteil der ersten MVPs.

## Kernfähigkeiten

1. Einen explizit ausgewählten Workspace sicher lesen.
2. Ziel, Kontext und Einschränkungen einer Aufgabe erfassen.
3. Einen strukturierten, prüfbaren Plan erzeugen.
4. Änderungen in einem isolierten Arbeitsbereich vorbereiten.
5. Tests und statische Prüfungen über erlaubte Befehle ausführen.
6. Diff, Prüfergebnisse und Risiken präsentieren.
7. Änderungen nur nach menschlicher Freigabe übernehmen.
8. Relevante Entscheidungen als lokale Markdown-Dateien dokumentieren.

## Nicht-Ziele der ersten Versionen

- Autonome Änderungen ohne Freigabe
- Allgemeiner Shell-Zugriff
- Zugriff außerhalb eines expliziten Workspace
- Cloud-Synchronisierung oder Telemetrie
- Bezahlte APIs oder produktive LLM-Aufrufe
- Plugin-Marktplatz, Multi-Agent-Schwärme oder selbstständige Deployment-Aktionen
- Vollständige IDE oder komplexe native macOS-App

## Erfolgskriterien für das erste Ende-zu-Ende-MVP

- Eine lokale Sitzung lässt sich für einen Test-Workspace starten.
- Der Agent kann freigegebene Textdateien lesen und einen deterministischen Änderungsvorschlag erzeugen.
- Vor jeder Änderung werden Plan, Diff und auszuführende Prüfungen angezeigt.
- Ablehnen verändert keine Workspace-Datei.
- Freigeben wendet exakt den angezeigten Patch an.
- Alle Aktionen erscheinen in einem lokalen, menschenlesbaren Audit-Log.
