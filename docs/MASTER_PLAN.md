# Sagent – Projektplan für einen Self-Building Personal AI Agent

Stand: 29.06.2026
Projektname: **Sagent**
Startplattform: **Mac-first**
Fokus: **Effizienz, Leistung, Kostenlosheit, Sicherheit und kontrollierte Selbst-Erweiterung**

---

## 1. Grundidee

**Sagent** soll ein persönlicher AI-Agent werden, der langfristig wie ein eigener Jarvis funktioniert, aber realistisch und sicher aufgebaut wird.

Der Agent soll später:

- mit mir schreiben können
- mit mir sprechen können
- Sprachbefehle verstehen
- Dateien lesen, analysieren und erstellen
- E-Mails schreiben
- im Internet recherchieren
- Kalender und To-dos verwalten
- mich proaktiv erinnern oder informieren
- auf Mac, Windows und Handy erreichbar sein
- eigene neue Funktionen entwickeln können
- große Aufgaben mit mehreren Teilagenten aufteilen können
- Apps und Funktionen bauen können
- sich iterativ mit menschlichem Feedback weiterentwickeln

Der wichtigste erste Schritt ist aber nicht direkt ein kompletter Jarvis, sondern:

> Zuerst bauen wir einen Developer-Agent-Core, der wie Codex/Cursor/Claude Code funktioniert und Sagent später selbst erweitern kann.

---

## 2. Leitprinzipien

Sagent soll nach folgenden Prinzipien gebaut werden:

1. **Local-first**
   - möglichst viel läuft lokal auf dem Mac
   - private Daten verlassen das Gerät nicht unnötig

2. **Kostenlos startbar**
   - keine Pflicht-API-Kosten
   - keine Cloud-GPU als Voraussetzung
   - Open-Source-Tools bevorzugt

3. **Effizient**
   - kleine, kontrollierbare Module
   - lokale Modelle erst später, wenn der Workflow steht
   - Modell-Router statt ein einziges riesiges Modell

4. **Leistungsfähig**
   - Developer-Agent zuerst
   - später lokale Coding-Modelle
   - später Memory, Web-Recherche, Datei-Analyse und Multimodalität

5. **Sicher**
   - keine unkontrollierte Selbstveränderung
   - keine Änderungen ohne Diff
   - keine kritischen Aktionen ohne Bestätigung
   - Sandbox + Approval wie bei Codex/Claude Code

6. **Iterativ**
   - erst MVP 1 bauen
   - danach Schritt für Schritt erweitern
   - jede neue Funktion wird geplant, getestet und freigegeben

---

## 3. Zielbild

Langfristig soll Sagent eine eigene App mit Chat-Oberfläche werden.

Der Agent soll sich anfühlen wie ChatGPT, aber stärker mit meinem Alltag und meinen Geräten verbunden sein.

Geplante Fähigkeiten:

- Chat
- Spracheingabe
- Sprachausgabe
- Datei-Upload
- Datei-Erstellung
- Code-Generierung
- App-Entwicklung
- Web-Recherche
- E-Mail-Entwürfe
- Kalender- und To-do-Integration
- Tages- und Wochenzusammenfassungen
- proaktive Benachrichtigungen
- später Telefonie
- später Gerätezugriff auf Mac, Windows und Handy

---

## 4. Wichtigste Priorität

Die wichtigste Priorität ist:

> Sagent soll zuerst ein eigener Developer-Agent werden, der neue Funktionen für Sagent bauen kann.

Das bedeutet:

- Ich gebe eine Aufgabe.
- Sagent analysiert das Projekt.
- Sagent erstellt einen Plan.
- Sagent schlägt Dateiänderungen vor.
- Sagent schreibt Code.
- Sagent schreibt Tests.
- Sagent führt Tests aus.
- Sagent zeigt Diff und Ergebnis.
- Ich bestätige oder lehne ab.
- Erst nach meiner Bestätigung werden Änderungen übernommen.

---

## 5. Realistische Selbst-Erweiterung

Sagent soll sich nicht unkontrolliert selbst verändern.

Stattdessen soll er wie ein kontrollierter Coding-Agent arbeiten.

### Gewünschter Workflow

```text
1. Nutzer gibt Aufgabe
2. Agent analysiert Projekt
3. Agent erstellt Plan
4. Agent erstellt Änderungsvorschlag
5. Agent zeigt betroffene Dateien
6. Agent schreibt Code in sicherem Kontext
7. Agent führt Tests aus
8. Agent zeigt Diff, Test-Ergebnis und Risiken
9. Nutzer bestätigt oder lehnt ab
10. Erst nach Bestätigung wird übernommen
11. Dokumentation und Memory werden aktualisiert
```

### Wichtig

```text
Planen darf er alleine.
Vorbereiten darf er kontrolliert.
Testen darf er kontrolliert.
Übernehmen darf er nur mit Bestätigung.
Kritische Aktionen brauchen immer Freigabe.
```

---

## 6. MVP 1 – Self-Building Developer-Agent

Der erste MVP soll noch nicht alle späteren Funktionen enthalten.

MVP 1 ist fertig, wenn Sagent lokal auf dem Mac als kontrollierter Developer-Agent funktioniert.

### MVP-1-Funktionen

- Projektordner lesen
- Projektdateien verstehen
- Aufgaben in Schritte zerlegen
- Änderungsvorschläge erstellen
- Dateien innerhalb des Projektordners erstellen
- Dateien innerhalb des Projektordners ändern
- Diffs anzeigen
- Tests ausführen
- Testergebnisse speichern
- Änderungen erklären
- Änderungen nur nach Bestätigung übernehmen
- Logs schreiben
- Dokumentation aktualisieren

### Nicht in MVP 1 enthalten

- echte E-Mail-Anbindung
- echte Kalender-Anbindung
- echte Telefonie
- vollständige Handy-App
- Vollzugriff auf Mac/Windows/Handy
- automatische Systemsteuerung
- unkontrollierte Selbstmodifikation
- vollständiges Langzeit-Memory mit Vektor-Datenbank

---

## 7. Mac-first Tech-Stack

Da wir auf dem Mac starten, wird der Stack auf lokale Entwicklung, gute Performance und einfache Bedienung ausgelegt.

---

## 7.1 Frontend / App-Oberfläche

### Phase 1: Next.js Web/PWA

Für den Start:

- Next.js
- React
- Tailwind CSS
- PWA-vorbereitet

Warum:

- schnell entwickelbar
- läuft im Browser
- funktioniert auf Mac, Windows und Handy
- kann später als App installiert werden
- kostenlos hostbar
- gute Basis für Chat-UI und Dashboard

### Phase 2: Tauri Desktop-App

Später:

- Tauri 2

Warum:

- native Desktop-App
- leichtgewichtiger als Electron
- gut für Mac, Windows und Linux
- später auch mobile Optionen möglich
- sicherer Zugriff auf lokale Funktionen möglich

### Entscheidung

```text
Phase 1: Next.js Web/PWA
Phase 2: Tauri Desktop-Shell
Phase 3: Windows/iOS/Android später
```

---

## 7.2 Backend / Agent-API

Für die lokale Agent-API:

- Python
- FastAPI

Warum:

- sehr gut für KI-Tools
- einfach lokal startbar
- gut für Datei-, Terminal-, Git- und Testzugriff
- gut kombinierbar mit LangGraph
- gut für spätere Python-Modelle und Agent-Workflows

### Struktur

```text
apps/agent-api = lokale FastAPI-App
```

---

## 7.3 Agent-Orchestrierung

Für Workflows:

- LangGraph

Aufgaben von LangGraph:

- Agent-Schritte steuern
- Tool-Aufrufe verwalten
- Status speichern
- Human-in-the-loop ermöglichen
- Freigaben einbauen
- lange Workflows kontrollieren
- später Multi-Agent-Orchestrierung ermöglichen

---

## 7.4 Python-Tooling

Für Python-Projektverwaltung:

- uv
- Python 3.11 oder 3.12
- pytest
- ruff
- pyright oder mypy

Warum uv:

- schnell
- moderne Python-Projektverwaltung
- gute Lockfiles
- gut für lokale Entwicklung
- ersetzt viele einzelne Python-Tools

---

## 7.5 JavaScript/Frontend-Tooling

Für das Monorepo und Frontend:

- pnpm
- pnpm workspaces
- Turborepo
- TypeScript

Warum:

- effizientere Paketverwaltung
- gute Monorepo-Struktur
- Frontend und gemeinsame Packages sauber organisierbar
- später schneller Build/Test/Lint durch Turborepo

---

## 7.6 Lokale Modelle später

Am Anfang wird kein lokales Modell erzwungen.

Zuerst bauen wir die Architektur mit Codex/ChatGPT/Claude Code-Unterstützung.

Später lokale Modelle:

- LM Studio
- Ollama
- MLX auf Apple Silicon
- Qwen3-Coder als Coding-Modell-Kandidat
- kleinere Qwen-/Gemma-/Phi-Modelle für Alltagstasks
- lokale Embedding-Modelle für Memory

### Reihenfolge

```text
Phase 1: Kein lokales Modell nötig
Phase 2: LM Studio als lokale OpenAI-kompatible API testen
Phase 3: Ollama für einfache lokale Modelle testen
Phase 4: MLX für Apple-Silicon-Effizienz testen
Phase 5: Modell-Router bauen
```

---

## 7.7 Coding-Agent später

Zum Bauen von Sagent nutzen wir zuerst:

- Codex
- alternativ Claude Code
- alternativ Cursor

Später kann Sagent selbst einen eigenen Developer-Agent bekommen.

Mögliche Bausteine später:

- OpenHands
- eigene LangGraph-Developer-Agent-Logik
- Qwen3-Coder
- Devstral
- lokale Modell-API über LM Studio/Ollama/MLX

---

## 8. Finaler Stack für MVP 1

```text
Projektname: Sagent
Startplattform: Mac
Frontend: Next.js + React + Tailwind
PWA: vorbereitet
Desktop später: Tauri 2
Backend: Python FastAPI
Agent-Orchestrierung: LangGraph
Python Tooling: uv, pytest, ruff, pyright/mypy
Frontend Tooling: pnpm, pnpm workspaces, Turborepo, TypeScript
Versionierung: Git + GitHub
Memory V1: Markdown-Dateien
Memory V2 später: Qdrant oder Chroma
Lokale Modelle später: LM Studio, Ollama, MLX
Coding-Modell später: Qwen3-Coder oder Devstral
Sicherheit: Sandbox + Approval wie Codex/Claude Code
```

---

## 9. Projektstruktur

Empfohlene Monorepo-Struktur:

```text
sagent/
│
├── apps/
│   ├── web/
│   │   └── Next.js Chat-/Dashboard-Oberfläche
│   │
│   └── agent-api/
│       └── Lokale Python-FastAPI-Agent-API
│
├── packages/
│   ├── agent-core/
│   │   └── Orchestrator, Tool-Router, Sicherheitslogik
│   │
│   ├── memory/
│   │   └── Memory-System, später Embeddings/Vektor-Suche
│   │
│   ├── tools/
│   │   └── Datei-, Git-, Terminal-, Browser-Tools
│   │
│   └── shared/
│       └── gemeinsame Typen und Hilfsfunktionen
│
├── docs/
│   ├── PROJECT.md
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   ├── SECURITY.md
│   ├── MEMORY.md
│   ├── AGENT_WORKFLOW.md
│   └── HANDOFF.md
│
├── tests/
│
├── .env.example
├── .gitignore
├── README.md
├── package.json
├── pnpm-workspace.yaml
├── turbo.json
└── pyproject.toml
```

---

## 10. Dokumentationssystem als Memory V1

Am Anfang wird das Memory nicht kompliziert gebaut.

Stattdessen nutzt Sagent ein sauberes Markdown-Projektgedächtnis.

### Dateien

#### README.md

- Projektbeschreibung
- lokale Startanleitung
- aktueller Status
- wichtigste Befehle

#### docs/PROJECT.md

- Ziel des Projekts
- langfristige Vision
- wichtigste Funktionen

#### docs/ARCHITECTURE.md

- Architektur
- Stack
- Module
- Datenfluss

#### docs/ROADMAP.md

- Meilensteine
- MVP 1 bis MVP 4
- langfristige Funktionen

#### docs/TASKS.md

- aktuelle Aufgaben
- offene Punkte
- nächste Schritte

#### docs/DECISIONS.md

- technische Entscheidungen
- Begründungen
- Datum der Entscheidung

#### docs/SECURITY.md

- Sicherheitsregeln
- Sandbox
- Approval
- erlaubte und verbotene Aktionen

#### docs/MEMORY.md

- Memory-Konzept
- welche Informationen gespeichert werden dürfen
- welche nicht

#### docs/AGENT_WORKFLOW.md

- Developer-Agent-Workflow
- Approval-Flow
- Tests
- Diffs

#### docs/HANDOFF.md

- Übergabe für zukünftige Agent-Sessions
- aktueller Projektstatus
- wichtige Hinweise

---

## 11. Sicherheitsmodell

Sagent soll ein Sicherheitsmodell ähnlich wie Codex/Claude Code bekommen.

### 11.1 Sandbox

Der Agent arbeitet nur in erlaubten Bereichen.

Standard:

- erlaubt: Sagent-Projektordner
- verboten: Systemordner
- verboten: private Ordner ohne Freigabe
- verboten: Desktop, Downloads, Documents, iCloud ohne explizite Freigabe
- verboten: `.env`, SSH-Keys, Tokens, Secrets
- verboten: gefährliche Shell-Befehle ohne Freigabe

### 11.2 Approval

Der Agent muss fragen bei:

- Datei löschen
- Datei außerhalb Workspace lesen
- Datei außerhalb Workspace schreiben
- Paket installieren
- Shell-Befehl ausführen
- Git push
- Git merge
- Netzwerkzugriff
- Secrets verwenden
- Zugriff auf private Daten
- Kalender ändern
- E-Mails senden
- System-Automation auf Mac

### 11.3 Allow-/Deny-Regeln

Prinzip:

```text
Deny gewinnt immer.
Was verboten ist, bleibt verboten, auch wenn eine andere Regel es erlaubt.
```

### 11.4 Git-Schutz

Regeln:

- nie direkt auf `main`
- immer auf Branch arbeiten
- Diff anzeigen
- Tests ausführen
- erst nach Bestätigung übernehmen
- keine Secrets committen
- `.env` niemals committen

### 11.5 Logs

Jede Aktion soll geloggt werden:

- Nutzeraufgabe
- Agent-Plan
- Tool-Aufrufe
- betroffene Dateien
- Änderungsvorschlag
- Approval-Status
- Test-Ergebnis
- finale Entscheidung

---

## 12. Developer-Agent-Workflow im Detail

### Schritt 1: Aufgabe

Nutzer gibt Aufgabe ein.

Beispiel:

```text
Baue eine Kalender-Integration ein.
```

### Schritt 2: Analyse

Sagent prüft:

- relevante Projektdateien
- Architektur
- Roadmap
- Tasks
- bestehende Module
- mögliche Risiken

### Schritt 3: Plan

Sagent erstellt:

- Ziel
- Umsetzungsschritte
- betroffene Dateien
- neue Dateien
- Tests
- Risiken
- benötigte Freigaben

### Schritt 4: Änderungsvorschlag

Sagent erstellt ein `ChangeProposal`.

Enthält:

- Beschreibung
- geplante Änderungen
- Risiko-Level
- betroffene Dateien
- benötigte Approvals

### Schritt 5: Approval

Status:

```text
pending
approved
rejected
needs_changes
```

### Schritt 6: Änderung

Erst nach Approval darf Sagent Änderungen vorbereiten oder schreiben.

### Schritt 7: Tests

Sagent führt nur erlaubte Testbefehle aus.

Beispiele:

```text
pytest
pnpm test
pnpm lint
pnpm build
```

### Schritt 8: Ergebnis

Sagent zeigt:

- Zusammenfassung
- Diff
- Test-Ergebnis
- bekannte Probleme
- nächste Schritte

### Schritt 9: Übernahme

Nur nach Bestätigung:

- Änderung wird übernommen
- Dokumentation wird aktualisiert
- Memory/HANDOFF wird aktualisiert

---

## 13. Kernmodule für MVP 1

### 13.1 TaskPlanner

Aufgabe:

- Nutzeraufgabe verstehen
- Aufgabe in Schritte zerlegen
- Plan erstellen

### 13.2 ChangeProposal

Aufgabe:

- geplante Änderungen beschreiben
- Risiko-Level setzen
- Approval-Anforderungen festlegen

### 13.3 ApprovalState

Aufgabe:

- Freigabe-Status verwalten

Statuswerte:

```text
pending
approved
rejected
needs_changes
```

### 13.4 WorkspaceGuard

Aufgabe:

- Zugriff nur innerhalb des Workspace erlauben
- Pfad-Ausbrüche blockieren
- `.env` und Secrets schützen
- gefährliche Dateioperationen verhindern

### 13.5 FileTool

Aufgabe:

- Dateien lesen
- Dateien erstellen
- Dateien ändern
- Dateien listen

Nur mit WorkspaceGuard.

### 13.6 DiffTool

Aufgabe:

- Änderungen sichtbar machen
- alte und neue Inhalte vergleichen
- Diff für Nutzer anzeigen

### 13.7 TestRunner

Aufgabe:

- erlaubte Testbefehle ausführen
- Ergebnisse speichern
- gefährliche Befehle blockieren

### 13.8 GitTool

Aufgabe später:

- Branch erstellen
- Status anzeigen
- Diff anzeigen
- Commit vorbereiten
- kein Push ohne Approval

### 13.9 Logger

Aufgabe:

- Aktionen protokollieren
- Freigaben speichern
- Testresultate speichern

---

## 14. API-Endpunkte für MVP 1

### Health

```http
GET /health
```

Antwort:

```json
{
  "status": "ok",
  "service": "sagent-agent-api"
}
```

### Aufgabe einreichen

```http
POST /agent/task
```

Aufgabe:

- nimmt Nutzeraufgabe entgegen
- erstellt einfache Antwort oder Task-ID

### Plan erstellen

```http
POST /agent/plan
```

Aufgabe:

- erstellt strukturierten Plan

### Aufgabe abrufen

```http
GET /agent/tasks/{id}
```

Aufgabe:

- zeigt aktuellen Status

### Approval geben

```http
POST /agent/approve
```

Aufgabe:

- Änderung freigeben oder ablehnen

### Tests ausführen

```http
POST /agent/run-tests
```

Aufgabe:

- erlaubte Tests ausführen

### Testresultate abrufen

```http
GET /agent/test-results/{id}
```

Aufgabe:

- Testlogs und Ergebnis anzeigen

---

## 15. Web-UI für MVP 1

Die erste Web-UI soll einfach bleiben.

### Bereiche

- Projektname
- Chat-/Task-Eingabe
- Antwortbereich
- Plananzeige
- Approval-Buttons
- Diff-Anzeige
- Test-Ergebnis
- Log-Anzeige

### Funktionen

- Aufgabe eingeben
- Plan anzeigen
- Änderungsvorschlag anzeigen
- Approve/Reject klicken
- Tests starten
- Ergebnis sehen

Noch nicht nötig:

- schöne finale UI
- Login
- Mobile Optimierung
- komplexe Einstellungen
- echte Modell-Auswahl

---

## 16. Git-Workflow

### Branch-Regel

Jede Aufgabe bekommt einen Branch:

```text
feature/name-der-funktion
fix/name-des-fehlers
docs/name-der-doku
```

### Main-Regel

```text
Nie direkt auf main ändern.
```

### Vor Merge

Pflicht:

- Tests bestanden
- Build bestanden
- Diff geprüft
- Zusammenfassung vorhanden
- Nutzer hat bestätigt

---

## 17. Roadmap

## MVP 1: Developer-Agent-Core

Ziel:

- Codex/Cursor-ähnlicher kontrollierter Developer-Agent

Funktionen:

- Projektstruktur
- FastAPI
- Next.js UI
- TaskPlanner
- ApprovalFlow
- WorkspaceGuard
- FileTool
- DiffTool
- TestRunner
- Dokumentation

---

## MVP 2: Echtes LLM und Modell-Router

Ziel:

- Sagent bekommt echte KI-Anbindung

Funktionen:

- Modell-Router
- lokale Modell-API
- LM Studio/Ollama testen
- optional OpenAI-kompatible Endpunkte
- erstes Coding-Modell testen
- Qwen3-Coder testen
- Devstral testen

---

## MVP 3: Memory V2

Ziel:

- besseres Gedächtnis

Funktionen:

- Qdrant oder Chroma
- lokale Embeddings
- semantische Suche
- Projektwissen durchsuchen
- alte Entscheidungen abrufen
- Task-Historie
- automatische Zusammenfassungen

---

## MVP 4: Datei- und Recherche-Agent

Ziel:

- produktive Arbeit mit Dateien und Internet

Funktionen:

- Markdown lesen/schreiben
- PDFs lesen
- Tabellen analysieren
- Code-Dateien analysieren
- Web-Recherche
- Playwright-Browser-Tool
- Quellen speichern
- Rechercheberichte erstellen

---

## MVP 5: Alltagstools

Ziel:

- persönliche Assistenz

Funktionen:

- E-Mail-Entwürfe
- Kalenderintegration
- Apple Erinnerungen
- To-dos
- Tageszusammenfassung
- Wochenzusammenfassung
- Push-Benachrichtigungen

---

## MVP 6: Voice und Telefonie

Ziel:

- Sprache und externe Kommunikation

Funktionen:

- Speech-to-Text
- Text-to-Speech
- Sprachnachrichten
- Anrufskripte
- später echte Telefonie
- Restaurantreservierungen
- Arzttermin-Anfragen

Telefonie kommt spät, weil sie komplexer und meistens nicht dauerhaft kostenlos ist.

---

## 18. Modellstrategie

Sagent nutzt langfristig keinen einzelnen festen KI-Kern, sondern einen Modell-Router.

### Phase 1

Kein eigenes Modell nötig.

- Codex/ChatGPT/Claude Code helfen beim Aufbau
- Sagent-Struktur wird vorbereitet
- Dummy-/Simulationslogik für Agent-Workflows

### Phase 2

Lokale Modell-API testen.

Optionen:

- LM Studio
- Ollama
- MLX

### Phase 3

Coding-Modelle testen.

Kandidaten:

- Qwen3-Coder
- Devstral
- andere gute Open-Weight-Coding-Modelle

### Phase 4

Spezialmodelle ergänzen.

- Coding-Modell
- kleines Chat-Modell
- Vision-Modell
- Embedding-Modell
- ggf. Speech-Modell

---

## 19. Cloud-Strategie

Für MVP 1 ist keine Cloud nötig.

### Start

- Mac lokal
- GitHub für Repository
- lokale API
- lokale Web-App

### Später

Mögliche kostenlose/limitierte Optionen:

- GitHub für Code, Issues, Actions
- Vercel oder Cloudflare Pages für Web-App
- Cloudflare Workers für kleine APIs
- Tailscale für sicheren Zugriff auf Geräte
- Qdrant Cloud Free für kleines Cloud-Memory
- Supabase Free für Auth/App-State, falls nötig

### Grundregel

```text
Cloud nur, wenn sie wirklich Nutzen bringt.
Local-first bleibt Standard.
```

---

## 20. Was bewusst später kommt

Diese Funktionen sind wichtig, aber nicht am Anfang:

- E-Mail-Anbindung
- Kalender-Anbindung
- Apple Erinnerungen
- vollständige Handy-App
- Vollzugriff auf Geräte
- proaktive Benachrichtigungen
- echte Telefonie
- große lokale Modelle
- Cloud-Hosting
- Multi-Agent-Orchester mit mehreren echten Agenten
- autonomes App-Bauen ohne Kontrolle

---

## 21. Start mit Codex

Der Start erfolgt mit Codex oder Claude Code.

Codex soll nicht direkt alles bauen, sondern kleine Aufgaben bekommen.

---

## 22. Erster Codex-Prompt

```text
Du bist mein Coding-Agent für das Projekt "Sagent".

Ziel:
Baue die erste saubere Projektbasis für einen local-first, Mac-first, self-building personal AI agent.

Sagent soll langfristig wie ein eigener Codex/Cursor/Claude-Code-Agent funktionieren:
Er soll Projektdateien lesen, Änderungen planen, Code schreiben, Tests ausführen, Diffs zeigen und Änderungen erst nach menschlicher Freigabe übernehmen.

Wichtig:
- Starte nicht mit einer komplexen App.
- Baue zuerst eine klare, saubere und dokumentierte Projektbasis.
- Keine kostenpflichtigen APIs.
- Keine echten LLM-Aufrufe.
- Keine gefährlichen Datei- oder Systemzugriffe.
- Alles soll lokal entwickelbar sein.

Bitte erstelle eine Monorepo-Struktur mit:

1. README.md
2. docs/PROJECT.md
3. docs/ARCHITECTURE.md
4. docs/ROADMAP.md
5. docs/TASKS.md
6. docs/DECISIONS.md
7. docs/SECURITY.md
8. docs/MEMORY.md
9. docs/AGENT_WORKFLOW.md
10. docs/HANDOFF.md
11. apps/web/ als Platzhalter für eine spätere Next.js/PWA-Oberfläche
12. apps/agent-api/ als Platzhalter für eine spätere Python-FastAPI-Agent-API
13. packages/agent-core/ als Platzhalter für Orchestrator, Tool-Router und Sicherheitslogik
14. packages/memory/ als Platzhalter für Memory-System
15. packages/tools/ als Platzhalter für Agent-Tools
16. packages/shared/ als Platzhalter für gemeinsame Typen/Hilfsfunktionen
17. .env.example
18. .gitignore
19. pnpm-workspace.yaml
20. package.json
21. turbo.json
22. pyproject.toml

Tech-Stack:
- Frontend: Next.js, React, Tailwind, TypeScript
- Backend: Python FastAPI
- Python Tooling: uv, pytest, ruff
- Monorepo: pnpm workspaces, Turborepo
- Agent-Orchestrierung später: LangGraph
- Memory V1: Markdown-Dateien
- Sicherheit: Sandbox + Approval wie Codex/Claude Code

Dokumentation:
- Schreibe in README.md eine verständliche Projektbeschreibung.
- Schreibe in ROADMAP.md die MVPs und ersten Meilensteine.
- Schreibe in SECURITY.md die Sicherheitsregeln.
- Schreibe in TASKS.md die nächsten konkreten Aufgaben.
- Schreibe in DECISIONS.md die ersten Architekturentscheidungen.
- Schreibe in AGENT_WORKFLOW.md den Developer-Agent-Workflow.
- Schreibe in HANDOFF.md eine Übergabe für zukünftige Agent-Sessions.

Am Ende:
- Gib eine Zusammenfassung.
- Liste alle erstellten Dateien.
- Erkläre, was als nächstes gebaut werden sollte.
```

---

## 23. Zweiter Codex-Prompt

```text
Baue jetzt die erste technische Minimalversion von Sagent.

Ziel:
Eine lokale Agent-API mit FastAPI und eine einfache Web-Oberfläche als Platzhalter.

Bitte erstelle:

1. apps/agent-api/
   - Python FastAPI App
   - Endpoint GET /health
   - Endpoint POST /agent/task
   - einfache Task-Verarbeitung als Platzhalter
   - strukturierte Response mit status, message, next_steps
   - pytest-Test für /health
   - pytest-Test für /agent/task

2. apps/web/
   - einfache Next.js App
   - Startseite mit Projektname "Sagent"
   - Chat-ähnliches Eingabefeld
   - Button zum Senden einer Aufgabe
   - Anzeige der Antwort von /agent/task
   - einfache Fehleranzeige

3. Dokumentation
   - README aktualisieren
   - lokale Startanleitung ergänzen
   - TASKS.md aktualisieren
   - HANDOFF.md aktualisieren

Wichtig:
- Keine externen kostenpflichtigen APIs.
- Keine echten Modellaufrufe.
- Nur Grundstruktur.
- Alles soll lokal startbar sein.
- Nutze pnpm für Frontend.
- Nutze uv für Python.
- Nutze pytest für Backend-Tests.
- Nutze ruff für Python-Linting.

Am Ende:
- Tests ausführen.
- Ergebnis dokumentieren.
- geänderte Dateien auflisten.
- nächste Schritte vorschlagen.
```

---

## 24. Dritter Codex-Prompt

```text
Erweitere die Agent-API um einen Developer-Agent-Workflow als sichere Simulation.

Ziel:
Sagent soll Aufgaben nicht direkt ausführen, sondern zuerst in Schritte zerlegen und eine Freigabe verlangen.

Baue:

1. TaskPlanner
   - nimmt eine Nutzeraufgabe entgegen
   - erstellt einen strukturierten Plan
   - enthält Ziel, Schritte, Risiken und nächste Aktionen

2. ChangeProposal
   - beschreibt geplante Dateiänderungen
   - enthält Risiko-Level
   - enthält benötigte Freigaben
   - enthält betroffene Dateien

3. ApprovalState
   - pending
   - approved
   - rejected
   - needs_changes

4. API-Endpunkte
   - POST /agent/plan
   - POST /agent/approve
   - GET /agent/tasks/{id}

5. Web-UI
   - Aufgabe eingeben
   - Plan anzeigen
   - Risiken anzeigen
   - Approve/Reject Buttons

6. Tests
   - Plan-Erstellung testen
   - Approval-Flow testen
   - ungültige Approval-Werte blockieren

Wichtig:
Noch keine echten Dateiänderungen.
Erst nur sicherer Workflow.

Am Ende:
- Tests ausführen.
- Diffs erklären.
- Risiken nennen.
- HANDOFF.md aktualisieren.
```

---

## 25. Vierter Codex-Prompt

```text
Erweitere den Developer-Agent-Workflow um sichere Dateioperationen im Projektordner.

Ziel:
Sagent darf nur innerhalb eines erlaubten Workspace-Ordners Dateien erstellen oder ändern.

Baue:

1. WorkspaceGuard
   - verhindert Zugriff außerhalb des Projektordners
   - blockiert absolute Pfade außerhalb des Workspace
   - blockiert Pfad-Traversal wie ../
   - blockiert sensible Dateien wie .env
   - blockiert SSH-Keys, Tokens und Secrets

2. FileTool
   - read_file
   - write_file
   - list_files
   - create_file

3. ChangeSet
   - sammelt geplante Änderungen
   - zeigt alte und neue Inhalte
   - erzeugt Diff

4. Approval-Pflicht
   - Dateiänderungen werden erst nach Approval geschrieben

5. Tests
   - Zugriff außerhalb Workspace muss fehlschlagen
   - .env darf nicht überschrieben werden
   - Pfad-Traversal muss blockiert werden
   - normale Dateiänderung nach Approval funktioniert

Am Ende:
- Tests ausführen.
- Sicherheitslogik erklären.
- geänderte Dateien auflisten.
- HANDOFF.md aktualisieren.
```

---

## 26. Fünfter Codex-Prompt

```text
Erweitere den Developer-Agent um sichere Test-Ausführung.

Ziel:
Nach Änderungen soll Sagent Tests ausführen können und das Ergebnis speichern.

Baue:

1. TestRunner
   - erlaubt nur definierte Testbefehle
   - z.B. pytest für agent-api
   - pnpm test für web, falls vorhanden
   - pnpm lint, falls vorhanden
   - keine beliebigen Shell-Befehle

2. TestResult
   - command
   - exit_code
   - stdout
   - stderr
   - passed
   - created_at

3. API
   - POST /agent/run-tests
   - GET /agent/test-results/{id}

4. UI
   - Button "Tests ausführen"
   - Anzeige von bestanden/fehlgeschlagen
   - Anzeige von Logs

5. Sicherheitsregeln
   - keine beliebigen Shell-Befehle
   - nur Allowlist-Kommandos
   - gefährliche Befehle blockieren

6. Tests
   - erfolgreicher Testlauf
   - fehlgeschlagener Testlauf
   - verbotener Befehl wird blockiert

Am Ende:
- Tests ausführen.
- alle Ergebnisse dokumentieren.
- HANDOFF.md aktualisieren.
```

---

## 27. Sechster Codex-Prompt

```text
Erweitere Sagent um Git-Diff- und Branch-Unterstützung.

Ziel:
Sagent soll Änderungen nicht einfach übernehmen, sondern Git-Diffs anzeigen und auf Branches arbeiten.

Baue:

1. GitTool
   - git status anzeigen
   - aktuellen Branch anzeigen
   - neuen Branch erstellen
   - Diff anzeigen
   - Commit vorbereiten, aber nicht automatisch pushen

2. Sicherheitsregeln
   - kein git push ohne Approval
   - kein merge ohne Approval
   - keine Änderungen direkt auf main
   - Warnung, wenn aktueller Branch main ist

3. API
   - GET /git/status
   - POST /git/branch
   - GET /git/diff

4. UI
   - Git-Status anzeigen
   - Diff anzeigen
   - Branch anzeigen

5. Tests
   - Branch-Regel testen
   - Diff-Ausgabe testen
   - Push/Merge bleibt blockiert

Am Ende:
- Tests ausführen.
- SECURITY.md aktualisieren.
- AGENT_WORKFLOW.md aktualisieren.
- HANDOFF.md aktualisieren.
```

---

## 28. MVP 1 ist fertig, wenn

MVP 1 gilt als fertig, wenn:

- Repository sauber strukturiert ist
- Web-UI lokal startet
- Agent-API lokal startet
- `/health` funktioniert
- Nutzer Aufgabe eingeben kann
- Sagent einen Plan erstellt
- Sagent Änderungsvorschlag erstellt
- Nutzer freigeben oder ablehnen kann
- Dateiänderungen nur im Workspace möglich sind
- `.env` und Secrets geschützt sind
- Sagent Diff anzeigen kann
- Sagent Tests ausführen kann
- Testresultate angezeigt werden
- Git-Status/Diff sichtbar sind
- keine gefährlichen Aktionen ohne Approval passieren
- Dokumentation aktuell ist
- HANDOFF.md für neue Sessions nutzbar ist

---

## 29. Konkrete nächste Schritte

1. GitHub-Repository erstellen:

```text
sagent
```

2. Codex oder Claude Code mit dem Repository verbinden.

3. Ersten Codex-Prompt ausführen.

4. Ergebnis prüfen.

5. Danach zweiten Prompt ausführen.

6. Schrittweise bis MVP 1 weiterbauen.

---

## 30. Zusammenfassung

Sagent wird nicht direkt als kompletter persönlicher Jarvis gebaut.

Stattdessen bauen wir zuerst den wichtigsten Kern:

> Einen sicheren, lokalen, Mac-first Developer-Agent, der wie Codex/Cursor/Claude Code funktioniert und Sagent später selbst kontrolliert erweitern kann.

Der Start ist bewusst klein:

- saubere Projektstruktur
- lokale API
- einfache Web-UI
- Agent-Workflow
- Approval-System
- sichere Dateioperationen
- Tests
- Git-Diff
- Dokumentation

Erst danach kommen:

- echte LLMs
- lokale Modelle
- Memory mit Qdrant/Chroma
- Web-Recherche
- Datei-Analyse
- E-Mail
- Kalender
- Handy-Zugriff
- Voice
- Telefonie

Das Projekt bleibt dadurch:

- effizient
- kostenlos startbar
- leistungsfähig erweiterbar
- sicher kontrollierbar
- realistisch umsetzbar
