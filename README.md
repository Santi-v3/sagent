# Sagent — Local-first AI Agent for macOS

> A personal software engineering project exploring AI agents, local large language models and human-in-the-loop automation.

**Focus:** AI Agents · Python / FastAPI · Next.js · Ollama · SQLite · Developer Automation

## Projektüberblick

**Problem:** KI-Assistenten sollen lokale Entwicklungsaufgaben unterstützen, ohne dass jeder Arbeitsschritt unkontrolliert ausgeführt oder Projektkontext ständig erneut eingegeben werden muss.

**Ansatz:** Sagent kombiniert eine lokale API, Weboberfläche, LLM-Anbindung, persistentes Memory und nachvollziehbare Werkzeugabläufe. Für Änderungen gibt es geprüfte Preview-/Freigabepfade. Ein zusätzlicher experimenteller Agent Loop ist ausdrücklich noch nicht für unbeschränkte oder produktive Nutzung abgesichert.

**Mein Schwerpunkt:** Konzeption und prototypische Implementierung einer lokalen KI-Agentenarchitektur mit Werkzeugsteuerung, Sicherheitspolicies und reproduzierbaren Entwicklungsschritten.

### Einstieg in das Projekt

- [Architektur](docs/ARCHITECTURE.md)
- [Sicherheit und bekannte Grenzen](docs/SECURITY.md)
- [Projektziel und Scope](docs/PROJECT.md)
- [Dokumentationsübersicht](docs/INDEX.md)

---

## Technische Details und lokaler Start

Sagent ist ein local-first, Mac-first Personal AI Agent. Der aktuelle Feature-Branch enthält eine lokale FastAPI, eine Next.js-Oberfläche, Ollama-Anbindung, SQLite-basiertes semantisches Memory sowie einen mehrstufigen Agent Loop mit Streaming und 16 Werkzeugen.

## Schnellstart

Voraussetzungen: macOS, Node.js 22+, pnpm 11+, Python 3.12 und uv.

```bash
pnpm install
uv sync --dev
pnpm dev
```

- Web: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8765`
- API-Dokumentation: `http://127.0.0.1:8765/docs`

Für einen Produktionsstart kann lokal `start.command` verwendet werden. Das Skript bricht ab, wenn Port 3000 oder 8765 bereits belegt ist.

## Aktueller Funktionsumfang

- deterministischer Plan-, Proposal- und Approval-Workflow
- sichere ChangeSet-basierte Code-Edit-API
- allowlist-basierte Testausführung und begrenzte Git-Funktionen
- feste Loopback-Profile für Ollama und LM Studio
- Modelljobs, Abbruch und Streaming
- persistentes Memory über SQLite und lokale Ollama-Embeddings
- Agent Loop mit Tool-Events, Conversation-Kontext und Memory-Injektion
- Cloud-Metadaten nur als deaktivierte Offline-Preview; `remote_http` bleibt blockiert

## Sicherheitsstatus

Die geprüften ChangeSet-, Test- und Git-Basispfade erzwingen enge Policies. Der experimentelle Agent Loop besitzt zusätzlich direkte Shell-, Schreib-, Apply- und Testadapter. Er arbeitet mit Limits, aber ohne echte Betriebssystem-Sandbox und ohne durchgängige externe Nutzerfreigabe. Nur in bewusst ausgewählten, vertrauenswürdigen lokalen Checkouts verwenden.

Verbindliche Details: [`docs/SECURITY.md`](docs/SECURITY.md).

## Qualität

```bash
pnpm check
pnpm build
uv run pytest -q
```

## Dokumentation

Beginne bei [`docs/INDEX.md`](docs/INDEX.md). Dort ist festgelegt, welche Datei für welches Thema die einzige aktive Quelle ist und wann sie aktualisiert werden muss.

## Lizenz

Noch nicht festgelegt. Bis eine Lizenzdatei hinzugefügt wird, bleiben alle Rechte vorbehalten.
