# Architekturentscheidungen

Dieses Dokument ist ein leichtgewichtiges Decision Log. Neue Entscheidungen erhalten eine fortlaufende Nummer, Datum, Status, Kontext und Konsequenzen.

## ADR-001: Local-first und Mac-first

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Sagent läuft zunächst vollständig lokal auf macOS. Netzwerk- und Cloud-Funktionen sind opt-in und außerhalb der ersten MVPs.
- **Konsequenz:** Lokale Installierbarkeit, Datenschutz und macOS-Sandboxing haben Vorrang vor Plattformbreite.

## ADR-002: Monorepo mit pnpm und Turborepo

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Frontend, API und gemeinsame Pakete leben in einem Repository. pnpm verwaltet JavaScript-Workspaces; Turborepo koordiniert Tasks.
- **Konsequenz:** Ein gemeinsamer Änderungsstand und zentrale Dokumentation; Python wird weiterhin mit uv verwaltet.

## ADR-003: Python für Agent-Core und API

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** FastAPI, Orchestrierung und sicherheitskritisches Tool-Routing werden in Python implementiert.
- **Konsequenz:** Gute Unterstützung für AI-Ökosysteme und Tests; Verträge mit TypeScript müssen explizit synchronisiert werden.

## ADR-004: Keine LLM-Abhängigkeit in den ersten Sicherheits-MVPs

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Read-, Plan-, Patch- und Approval-Flows werden zuerst deterministisch implementiert und getestet.
- **Konsequenz:** Sicherheitsmechanismen bleiben unabhängig von Modellverhalten und können reproduzierbar geprüft werden.

## ADR-005: Markdown als Memory V1

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Langzeitkontext wird zunächst in menschenlesbaren Markdown-Dateien gespeichert.
- **Konsequenz:** Einfach zu prüfen und zu versionieren; semantische Suche und Konfliktauflösung kommen später.

## ADR-006: Explizite Freigabe ist eine serverseitige Fähigkeit

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Eine Freigabe ist an Proposal-Hash, Workspace, Aktion und Ablaufzeit gebunden. Die UI allein kann keine Änderung autorisieren.
- **Konsequenz:** Veränderte Vorschläge benötigen eine neue Freigabe; Replay und UI-Bypass werden erschwert.

## ADR-007: LangGraph erst bei nachgewiesener Notwendigkeit

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Die ersten Zustände werden als einfache, getestete Zustandsmaschine gebaut. LangGraph wird eingeführt, wenn Verzweigungen, Wiederaufnahme oder Persistenz es rechtfertigen.
- **Konsequenz:** Geringere Anfangskomplexität ohne die spätere Technologieoption zu verlieren.

## ADR-008: Der Projektplan ist die strategische Kontextquelle

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** `docs/MASTER_PLAN.md` definiert Vision, Zielbild, MVP-Reihenfolge und langfristigen Scope. Fokussierte Dokumente dürfen Details präzisieren, aber strategische Abweichungen müssen sichtbar als neue Entscheidung dokumentiert werden.
- **Konsequenz:** Neue Agent-Sessions lesen zuerst den Masterplan. `SECURITY.md` bleibt für Schutzregeln verbindlich; bei Unklarheit gilt die strengere Regel. `TASKS.md` und `HANDOFF.md` bilden nur den aktuellen Ausschnitt ab.

## ADR-009: Feature-Branch, Push und Pull Request sind der Standardabschluss

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Codex arbeitet pro Aufgabe auf einem Feature-Branch, testet, committet, pusht den Feature-Branch und erstellt einen Pull Request gegen `main`. Nur der Nutzer darf den Merge freigeben.
- **Konsequenz:** Feature-Branch-Push und PR-Erstellung gelten als dauerhaft autorisierte Abschlussaktionen. Direkte Arbeit oder Pushes auf `main`, Force-Push, Auto-Merge und Merge ohne ausdrückliche Nutzerbestätigung bleiben verboten. Diese neuere Entscheidung präzisiert abweichende Git-Regeln im Masterplan.

## ADR-010: Datei-Freigaben sind inhaltsgebundene ChangeSets

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Dateiänderungen werden zuerst mit kanonischen relativen Pfaden, altem und neuem Inhalt sowie Unified Diff vorbereitet. Die Freigabe bindet sich an einen SHA-256-Hash dieses exakten ChangeSets. Erst danach erzeugt der Core prozessinterne, HMAC-signierte Schreibnachweise für die enthaltenen Dateioperationen.
- **Konsequenz:** Ein geänderter Pfad, Inhalt, Operationstyp oder Ausgangszustand entwertet die Freigabe. ChangeSets werden nur einmal angewendet. Die Zustände liegen in MVP 1.C noch ausschließlich im Prozessspeicher; Persistenz und Ablaufzeiten folgen vor einer produktiven Nutzung.

## ADR-011: Testausführung erfolgt nur über sichtbare, feste Profile

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Die API akzeptiert keine Befehle oder Argumentlisten aus Requests. Sie bietet ausschließlich serverseitig registrierte Profile an. Ein Lauf benötigt einen bereits freigegebenen Task, `confirmed=true` und den unverändert zurückgesendeten Anzeigebefehl. Der Prozess startet als Argumentliste ohne freie Shell.
- **Konsequenz:** Unbekannte Profile und veränderte Befehle werden vor Prozessstart blockiert. Timeout, Prozessgruppe, CPU, Dateideskriptoren, Umgebung, Loggröße, Redaction und Ergebnisanzahl sind begrenzt. Da Repository-Tests selbst Code ausführen, bleibt der Runner bis zu einer echten macOS-Sandbox nur für bewusst geprüfte lokale Workspaces freigegeben.

## ADR-012: Git-Inspektion und Git-Mutation bleiben getrennt

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** MVP 1.E stellt Branch, Status und einen begrenzten, Secret-redigierten Diff über feste Git-Argumentlisten bereit. Als einzige Mutation darf ein ausdrücklich bestätigter, policy-konformer lokaler Feature-Branch erstellt werden. Eine Commit-Vorbereitung erzeugt nur Metadaten, die an den sichtbaren Diff-Hash gebunden sind; sie staged und committet nicht. Push und Merge sind im Tool immer blockiert.
- **Konsequenz:** Die Weboberfläche kann den Repository-Zustand prüfbar machen, besitzt aber keine Remote-Aktion. Sensible, gekürzte oder nachträglich veränderte Diffs blockieren die Commit-Vorbereitung. Ein späterer Commit-, Push- oder Merge-Flow benötigt eigene serverseitige Approval-Verträge und neue negative Sicherheitstests. Der beaufsichtigte Codex-Repository-Abschluss aus ADR-009 bleibt davon getrennt.

## ADR-013: Der Modell-Router erzwingt Fähigkeiten, Provenienz und Transportgrenzen

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Modellintegration beginnt mit einem provider-neutralen Text-Completion-Vertrag. Eingabeteile behalten ihre Herkunft, Fähigkeiten werden über feste Routen gewählt und jede Adapterbeschreibung deklariert eine Transportklasse. Der Router erlaubt zunächst ausschließlich In-Process-Adapter. Antworten sind immer untrusted und können keine Tools autorisieren oder repräsentieren.
- **Konsequenz:** Der deterministische Fake ermöglicht API- und Sicherheitstests ohne Modellserver. LM Studio, Ollama oder andere OpenAI-kompatible Server benötigen einen eigenen Loopback-Transport mit URL-, Redirect-, Timeout-, Streaming- und Größen-Policies. Remote-Endpunkte bleiben außerhalb des local-first Scopes, bis eine spätere Entscheidung sie ausdrücklich zulässt.

## ADR-014: Lokale Modelle nutzen feste Providerprofile statt frei wählbarer URLs

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Der erste echte Modelltransport unterstützt nur den gemeinsamen OpenAI-kompatiblen Chat-Completions-Vertrag von LM Studio und Ollama. LM Studio ist an den Profilport `1234`, Ollama an `11434` gebunden. Ein Request wählt nur einen zuvor registrierten Adapter; URL, Port, Modell und Provider stammen ausschließlich aus der beim Prozessstart fixierten Konfiguration.
- **Konsequenz:** SSRF auf andere lokale Dienste, DNS-/Redirect-Ausbrüche, Request-Credentials und frei injizierbare Endpoints bleiben blockiert. Abweichende Ports, Authentifizierung, Streaming, Responses API, Tools und Remote-Provider benötigen jeweils eine neue Architektur- und Sicherheitsentscheidung.

## ADR-015: Modellgenerierungen sind begrenzte, aktiv abbrechbare Jobs

- **Status:** Angenommen
- **Datum:** 2026-06-29
- **Entscheidung:** Längere lokale Modellaufrufe erhalten einen eigenen In-Memory-Job-Lebenszyklus. Ein thread-sicherer Cancellation-Token wird bis in den HTTP-Adapter propagiert und schließt bei Abbruch aktive Ressourcen. Job-Snapshots enthalten keinen Prompt und Adapterfehler werden generisch redigiert.
- **Konsequenz:** UI und weitere Clients können Status und Abbruch später ohne Zugriff auf Endpoint oder Prompt anbieten. Parallelität und Historie bleiben begrenzt; API-Neustart verwirft Jobs. Persistenz, Resume und verteilte Worker benötigen eine spätere Entscheidung.
