# Projektdefinition

> **Pflegebereich:** stabiles Produktziel und bewusster Scope. Fortschritt gehört in `ROADMAP.md`.

## Vision

Sagent ist ein lokal laufender persönlicher Agent für macOS. Er verbindet Chat, Projektkontext, lokale Modelle, Memory und kontrollierte Entwicklungswerkzeuge in einer Oberfläche.

## Zielgruppe

Zunächst ist Sagent ein persönliches Einzelbenutzer-Werkzeug. Mehrbenutzerbetrieb, gehostete Plattform und öffentliche Plugin-Ausführung sind nicht Teil des aktuellen Scopes.

## Kernfähigkeiten

- lokalen Projektkontext lesen und durchsuchen
- lokale Modelle über feste Loopback-Profile nutzen
- Gespräche und relevante Informationen lokal speichern
- Änderungen über einen geprüften Preview-/Approval-Pfad vorbereiten
- definierte Tests und begrenzte Git-Operationen ausführen
- im experimentellen Agent-Modus mehrere Tools iterativ verwenden

## Produktgrenzen

- Cloud-Ausführung und `remote_http` bleiben deaktiviert.
- Git-Push und Merge sind nicht im Sagent-Tool implementiert.
- Der geprüfte Basispfad bleibt human-in-the-loop.
- Der experimentelle Agent Loop besitzt derzeit stärkere lokale Rechte als der Basispfad und ist nicht produktionsreif.
- Es gibt keine echte Betriebssystem-Sandbox für die freie Shell.

## Erfolgskriterium der aktuellen Phase

Ein Nutzer kann Sagent lokal starten, mit einem lokalen Modell chatten, Memory verwenden und Tool-Aktivität nachvollziehen. Vor einer produktiven Nutzung des Agent Loops müssen Pfadgrenzen, Approval und Prozessisolation technisch gehärtet werden.
