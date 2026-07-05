# Sagent

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
