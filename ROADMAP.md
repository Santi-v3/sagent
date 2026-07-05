# Sagent – Roadmap & Planung

## Vision: Persönlicher KI-Assistent (JARVIS für Entwickler)

> *"Sagent wird dein persönlicher KI-Assistent – immer da, immer lernend, immer hilfreich.  
> Wie JARVIS für Tony Stark, nur für dich und deine Projekte."*

**Der Name bleibt Sagent.** JARVIS ist nur die Vision – die Richtung, nicht der Name.

### Was JARVIS ausmacht – und wie Sagent dahin kommt

| JARVIS-Eigenschaft | Sagent heute | Sagent morgen |
|-------------------|-------------|---------------|
| **Natürliche Sprache** | Chat-Interface | Vollständige Konversation, Kontext über Sessions |
| **Proaktiv handeln** | Reagiert nur auf Tasks | Erkennt selbstständig Probleme + schlägt Lösungen vor |
| **Alles steuern** | Bash + Dateisystem | Alle APIs + Tools via MCP + Self-built Extensions |
| **Selbst verbessern** | – | Fehlende Fähigkeiten selbst einbauen (Killer-Feature) |
| **Überall verfügbar** | Desktop (macOS) | Handy + Laptop + Web + Server |
| **Sprache** | – | Whisper (Input) + TTS (Output) |
| **Visualisierung** | Text-Chat | HUD-ähnliche UI, Charts, Diff-Viewer, Echtzeit-Dashboard |
| **Persönlichkeit** | – | Konfigurierbarer Charakter, Humor, Stil |
| **Projekt-Kontext** | – | Weiß immer an welchem Projekt du arbeitest |
| **Erinnert sich** | Chat-Verlauf | Vektor-Memory: Entscheidungen, Preferences, Wissen |

### Der Weg

```
Heute ────→ Pilot (MVP) ────→ Agent ────→ JARVIS
  │            │                  │             │
  │          MCP + Tools       Extensions    Vollständig
  │          Lokale Modelle    Self-Build    autonom
  │          Chat              Sprache       proaktiv
  │                            Multi-Device  allgegenwärtig
```

---

## Status Quo (Juli 2026)

- Lokale Modelle via Ollama (gemma4, qwen2.5-coder) voll funktionsfähig
- Remote Ollama-Server via OpenAI-kompatiblen Endpoint konfigurierbar
- Agent Loop mit Tool Calling (Git, Tests, Terminal, File System)
- Safety Levels (Vorsichtig / Ausgewogen / Vollzugriff)
- Auto-Fallback bei nicht verfügbaren Modellen
- ProviderTracker für Rate-Limits
- Full-Page Settings mit eigener Navigation
- Intelligentes Task-Routing geplant: lokale Analyse → Entscheidung lokal/cloud

---

## 0. ToolRegistry – Komplett-Überholung (P0)

### Aktuelle Probleme

| Problem | Details |
|---------|---------|
| **TOOL_CALL Parsing** | Regex `^TOOL_CALL:\s*(\w+)\s*\n(.*?)` ist fragil: kein Multi-Tool, kein Structured Output, kein Streaming |
| **Kein JSON Schema Validation** | Parameter werden raw per `**kwargs` an Handler übergeben – keine Typesicherheit, keine Validierung |
| **System-Prompt hardcoded** | Deutsch, nicht konfigurierbar, keine dynamische Anpassung pro Conv |
| **Handler-Interface** | `Callable[..., str]` – kein strukturiertes Ergebnis, kein Status-Code, kein Stream |
| **Tool Discovery** | Keine Möglichkeit für externe Tools (Plugins/MCP) |
| **Tool Chaining** | Kein Pipe/Chain – jedes Tool läuft isoliert |
| **Sicherheit** | Keine granulare Permission pro Tool (nur globaler Safety-Level) |

### Ziel-Architektur

```
MCP-Standard (Model Context Protocol)
│
├── Eingebaut: Sagent-native Tools (bash, write, edit, git, tests, search)
│   └── Werden als MCP-Server bereitgestellt
│
├── Plugins: Externe MCP-Server
│   ├── opencode-tools (falls opencode MCP-Server bereitstellt)
│   ├── openclaw-tools
│   └── Community-MCP-Server (Docker, Kubernetes, Browser, etc.)
│
└── Tool-Registry mit:
    ├── JSON Schema Validation (json-schema)
    ├── Structured Output (TypedDict/Dataclass)
    ├── Tool-Chaining (Pipe stdout→stdin zwischen Tools)
    ├── Granulare Permissions (pro Tool: allow/ask/deny)
    └── Rate-Limiting pro Tool
```

### Konkrete Tasks

1. ToolHandler-Interface auf `StructuredTool` umstellen (Pydantic/JSON Schema)
2. Tool-Parsing von Regex auf `Model.parts` umstellen (ModelRequest enthält schon Tool-Calls)
3. MCP-Client in Sagent integrieren (Tool- und Resource-Provider)
4. Bestehende Tools (bash, write, edit, git) als MCP-Server wrappen
5. Permission-System: allow/ask/deny pro Tool + pro Session

---

## 1. Modell-Unterstützung

### Kurzfristig (1-2 Wochen)

| Feature | Details |
|---------|---------|
| **Modelle direkt in Sagent verwalten** | Download/Install von Modellen via UI (Ollama pull), Statusanzeige |
| **Mehrere Ollama-Instanzen** | Mehrere Remote-Ollama-Endpoints parallel (z.B. Server + NAS + Local) |
| **Modell-Vergleich** | Side-by-Side Output zweier Modelle für dasselbe Prompt |
| **Modell-Einstellungen pro Conv** | Temperature, Max Tokens, System Prompt pro Chat |
| **LM Studio / llama.cpp Support** | Auch OpenAI-kompatibel, nur anderer Default-Endpoint |
| **Intelligent Task Routing** | Lokales Modell analysiert Task-Komplexität → routed an passendes Modell (lokal/cloud) |

### Mittelfristig (1-2 Monate)

| Feature | Details |
|---------|---------|
| **Native Provider-Plugins (MCP)** | Jeder Provider (Ollama, OpenAI, Anthropic, Google) als MCP-Resource |
| **Vision/Multi-Modal** | Bilder analysieren (via gemma4 vision oder LLaVA) |
| **Embedding-Modelle** | Für RAG / Vektorsuche – nomic-embed-text, etc. |

### Langfristig

| Feature | Details |
|---------|---------|
| **Model Fine-Tuning** | LLM lokal auf eigenen Daten fine-tunen via QLoRA |
| **Spektrum / MoE Management** | Spezialisierte Sub-Modelle für verschiedene Fähigkeiten |
| **Self-Improving Router** | Router lernt aus vergangenen Tasks, optimiert Modell-Wahl automatisch |

---

## 2. Agent Loop & Tools

### Kurzfristig

| Feature | Details |
|---------|---------|
| **Tool-Whitelist pro Conv** | Welche Tools darf der Agent in diesem Chat nutzen? |
| **Tool-Ergebnis Vorschau** | Git-Diff, Terminal-Output vor Übernahme anzeigen |
| **Batch-Execution** | Mehrere Tasks nacheinander planen + ausführen |
| **Abbruch + Rollback** | Agent-Task abbrechen und Änderungen rückgängig machen |

### Mittelfristig

| Feature | Details |
|---------|---------|
| **Artefakte** | Agent erstellt Dateien (Code, Doku, Configs) – werden im Chat angezeigt und können direkt übernommen werden |
| **Multi-Agent** | Spezialisierte Sub-Agents (Code-Review-Agent, Test-Agent, Search-Agent) |
| **Human-in-the-Loop** | Agent fragt bei Unsicherheit nach, statt einfach weiterzumachen |
| **Session Management** | Agent läuft im Hintergrund, Benachrichtigung bei Fertigstellung |

### Langfristig

| Feature | Details |
|---------|---------|
| **Autonome Modus** | Agent arbeitet selbstständig an Issue/Ticket, erstellt PR |
| **CI/CD Integration** | Agent in GitHub Actions / GitLab CI einbinden |
| **Deployment Agent** | Automatisches Build + Deploy auf Server/Cloud |

---

## 3. Memory & Kontext

### Kurzfristig

| Feature | Details |
|---------|---------|
| **Chat-Verlauf verdichten** | Lange Konversationen automatisch zusammenfassen |
| **Projekt-Kontext** | Welches Projekt ist aktiv? README, git log, package.json einlesen |
| **Session Memory** | Agent merkt sich Entscheidungen innerhalb einer Session |

### Mittelfristig

| Feature | Details |
|---------|---------|
| **Vektor-Memory (RAG)** | Semantische Suche über alte Chats, Entscheidungen, Dokumentation |
| **Tool Memory** | Agent merkt sich, wie Tools funktionieren (Tool-Learning) |
| **User Preferences** | Persönliche Einstellungen pro Projekt (Sprache, Code-Style, etc.) |

---

## 4. UI/UX

### Kurzfristig

| Feature | Details |
|---------|---------|
| **Dark Mode** | Vollständige Theme-Unterstützung |
| **Code Syntax Highlighting** | In Chat-Antworten |
| **Diff-Viewer** | Änderungen visuell vergleichen (vorher/nachher) |
| **Modell-Status aktiv** | Laufende Token/s, geschätzte Zeit, Kosten (bei Cloud) |

### Mittelfristig

| Feature | Details |
|---------|---------|
| **Split View** | Chat + Code Editor nebeneinander |
| **Drag & Drop Dateien** | Dateien direkt in den Chat ziehen |
| **Audio-Input** | Spracheingabe via Whisper (lokal) |
| **Desktop Notifications** | Agent fertig, Fehler, Genehmigung erforderlich |

---

## 5. Architektur & Deployment

| Bereich | Kurzfristig | Mittelfristig |
|---------|-------------|---------------|
| **Packaging** | `.app` Bundle (macOS) | Windows + Linux Support |
| **Updates** | Auto-Update via `update.command` | Built-in Updater (Sparkle/electron-updater) |
| **Backend** | FastAPI single-process | Task Queue (ARQ/Celery) für Hintergrund-Jobs |
| **Datenhaltung** | SQLite + localStorage | Postgres + S3 für Artefakte |
| **Auth** | Keine (lokaler Desktop-Client) | Optional: SSO / API-Key für Team-Nutzung |

---

## 6. opencode / openclaw – Integration oder nicht?

**Kurze Antwort: Nicht direkt integrieren, sondern MCP-Standard adoptieren.**

### Warum nicht opencode einbauen?

| Aspekt | opencode | Sagent |
|--------|----------|--------|
| **Interface** | CLI (stdin/stdout) | Desktop-App (Electron) |
| **Tool-System** | Eigenes Permission/Approval-System | Eigene ToolRegistry |
| **Use Case** | Coding-Tasks in Terminal | Lokaler KI-Assistent mit GUI |
| **Lizenz** | Apache 2.0 | Noch offen |

Statt opencode zu fork-en oder zu integrieren, sollten **beide MCP unterstützen**. Dann kann Sagent Tools von opencode nutzen, ohne Abhängigkeiten.

### OpenClaw?

OpenClaw ist ein spezialisierter "One-Person-Company"-Agent. Interessant als Inspiration für den **Multi-Agent**- und **Artefakt**-Bereich, aber nicht als direkte Abhängigkeit. Auch hier: MCP erlaubt Kompatibilität ohne Integration.

### Fazit

| Priorität | Strategie |
|-----------|-----------|
| **P0** | Eigene ToolRegistry auf MCP-Standard umstellen (kein Fork, kein Vendor-Lock) |
| **P1** | MCP-Client: externe MCP-Server einbinden können |
| **P2** | Sagent-native Tools als MCP-Server publizieren (dann auch von opencode nutzbar) |

---

## 7. Modell-Empfehlungen für Sagent

### Free Cloud (via API-Key)

| Anbieter | Modelle | Stärken | Limit | Setup |
|----------|---------|---------|-------|-------|
| **Groq** | `llama-3.3-70b`, `mixtral-8x7b`, `gemma2-9b` | Sehr schnell, zuverlässig, kein Guthaben | 30 req/min | Key von console.groq.com |
| **Together AI** | `Mixtral`, `Qwen2`, `DeepSeek` | Gute Modell-Auswahl | $1 free Credit | Key von together.ai |
| **OpenAI** | `gpt-4o`, `o3`, `o4-mini` | Frontier-Modelle, Reasoning | Pay-per-Token | platform.openai.com |
| **Anthropic** | `claude-sonnet-4`, `claude-haiku-3.5` | Bester Coding/Reasoning | Pay-per-Token | console.anthropic.com |

### Kategorien (Ollama – nach Aufgabe optimiert)

#### Embedding (alle klein, lokal problemlos)

| Modell | Parameter | Pulls | Stärken |
|--------|-----------|-------|---------|
| **nomic-embed-text** | – | 77.1M | Am schnellsten, populärster Embedder |
| **mxbai-embed-large** | 335M | 12.2M | Bestes Quality/Size-Verhältnis |
| **bge-m3** | 567M | 5M | Beste Mehrsprachigkeit, Multi-Granularität |
| **snowflake-arctic-embed2** | 568M | 416K | Neuester Frontier-Embedder (multilingual) |
| **qwen3-embedding** | 0.6b–8b | 2.3M | Neueste Qwen-Familie, mehrere Größen |
| **all-minilm** | 22M/33M | 3.2M | Extrem leicht, reicht für Basis-RAG |

#### Vision (Bildanalyse, OCR, multimodal)

| Modell | Parameter | Pulls | Stärken |
|--------|-----------|-------|---------|
| **gemma4** | 12b–31b | 16.8M | Allrounder: Vision + Tools + Thinking in einem |
| **qwen3.5** | 0.8b–122b | 14.7M | Exzellent multimodal, viele Größen |
| **qwen3-vl** | 2b–235b | 4.3M | Dediziertes Vision-Language-Modell |
| **glm-ocr** | – | 6M | Bestes Modell für Dokument-OCR |
| **deepseek-ocr** | 3b | 482K | Token-effizientes OCR |
| **minicpm-v4.6** | 1b | 11.4K | Extrem leicht, für Phone/Edge |

#### Tools (Agentic, Coding, Tool-Calling)

| Modell | Parameter | Pulls | Stärken |
|--------|-----------|-------|---------|
| **gemma4** | 12b–31b | 16.8M | Frontier Agentic Workflows + Tool-Use |
| **qwen3.5** | 9b–35b | 14.7M | Exzellentes Tool-Calling, viele Größen |
| **qwen3.6** | 27b–35b | 3.5M | Upgrades: Agentic Coding, Thinking-Preservation |
| **glm-5.1** | cloud (744B/40B act.) | 2.3M | #1 auf SWE-Bench Pro (cloud, API-key) |
| **kimi-k2.7-code** | cloud | 70.8K | Bester Coding-Agent, 30% weniger Thinking-Tokens |
| **granite4.1** | 3b–30b | 222K | Apache 2.0, Enterprise Tool-Use, JSON-Output |
| **laguna-xs-2.1** | 33B MoE (3B aktiv) | 2.6K | Speziell für lokales agentic coding, nagelneu |
| **north-mini-code-1.0** | 30B MoE (3B aktiv) | 18K | Von Cohere für agentic SE gebaut |
| **glm-4.7-flash** | 30B | 1.3M | Stärkstes in 30B-Klasse, tools + thinking |

#### Thinking (Reasoning, komplexe Problemlösung)

| Modell | Parameter | Pulls | Stärken |
|--------|-----------|-------|---------|
| **gemma4** | 12b–31b | 16.8M | Starkes Reasoning + alles andere |
| **qwen3.5** | 9b–122b | 14.7M | Thinking Mode integriert |
| **qwen3.6** | 27b–35b | 3.5M | Thinking-Preservation verbessert |
| **deepseek-v4-flash** | 284B/13B act. | 192K | Effizientes Reasoning (braucht RAM) |
| **deepseek-v4-pro** | cloud | 187K | Frontier-Reasoning (cloud) |
| **glm-5.1** | cloud | 2.3M | Reasoning + Agentic (SWE-Bench #1) |
| **mistral-medium-3.5** | 128B | 138K | Vereinigt Reasoning + Instruction + Coding |
| **glm-4.7-flash** | 30B | 1.3M | Lokal-freundliches Thinking |

### Optimale Strategie (Usage-Limit-schonend)

Statt viele spezialisierte Modelle zu laden, reichen **3–4 Modelle** für alle Rollen:

```
Role                    │ Empfohlenes Modell                  │ Begründung
────────────────────────┼─────────────────────────────────────┼────────────────────────────────
Swiss Army Knife        │ gemma4:12b                          │ Vision + Tools + Thinking –
                        │                                     │  ein Model für 80% aller Tasks
Lightning Agentic       │ laguna-xs-2.1                       │ MoE, nur 3B aktiv, ideal für
                        │  oder north-mini-code-1.0           │  Coding-Agenten lokal
Leichtes Reasoning      │ glm-4.7-flash                       │ 30B, lokal lauffähig,
                        │  oder qwen3.5:9b                    │  tools + thinking
Embedding (RAG)         │ nomic-embed-text (schnell)          │ Klein, schnell
                        │  + mxbai-embed-large (Qualität)     │
Cloud-Fallback          │ Groq (llama-3.3-70b)                │ Zuverlässigster Free-Cloud,
                        │  + Kimi K2.7 Code (bester Coder)    │  kein Usage-Limit
```

### Priorisierung für Sagent

```
Lokal installieren (nach Relevanz)
├── gemma4:12b ──── Allrounder, läuft schon → Primary Model
├── glm-4.7-flash ─── 30B, tools + thinking → Router/Analyzer
├── laguna-xs-2.1 ─── MoE, 3B aktiv → Agentic Coding
├── nomic-embed-text ─── Embedding → RAG
├── north-mini-code-1.0 ─── Cohere agentic SE → testen
├── qwen3.6 ─── upgraded agentic coding → testen
└── deepseek-v4-flash ─── Reasoning (nur mit RAM)

Cloud-Fallback
├── Groq (llama-3.3-70b) ─── zuverlässigster Free-Cloud-Provider
├── Kimi K2.7 Code ─── bester Coding-Agent (via API)
├── GLM-5.1 ─── #1 SWE-Bench Pro (via API)
└── DeepSeek-V4-Pro ─── Frontier-Reasoning (via API)
```

---

## 8. Intelligent Task Routing (Smart Dispatch)

### Vision

Wenn der User eine Aufgabe schreibt, analysiert ein **leichtes lokales Modell** sofort:
- Wie komplex ist diese Aufgabe?
- Was wird benötigt? (Coding, Reasoning, Recherche, Datei-Operationen, Vision?)
- Wie viele Tokens/Schritte werden voraussichtlich gebraucht?

Basierend auf dieser Analyse wird die Aufgabe entweder **lokal** (schnell, kein Usage-Limit) oder an ein **Cloud-Modell** (leistungsstärker bei Komplexität) weitergeleitet.

### Flow

```
User: "Schreib mir eine REST-API in Python mit FastAPI"

                         ┌─────────────────────────────┐
                         │ Task Analyzer (lokal)        │
                         │ z.B. glm-4.7-flash:30b      │
                         │ oder gemma4:12b              │
                         └──────────┬──────────────────┘
                                    │
                        ┌───────────┴───────────┐
                        ▼                       ▼
              ┌─────────────────┐    ┌──────────────────┐
              │ Einfach / Lokal  │    │ Komplex / Cloud   │
              │                 │    │                   │
              │ • Fragen        │    │ • Große Codebases │
              │ • Datei-Suchen  │    │ • Architecture    │
              │ • Kleine Edits  │    │ • Refactoring     │
              │ • Git-Status    │    │ • Reasoning       │
              │ • Bash-Befehle  │    │ • Multi-Step      │
              └────────┬────────┘    └────────┬─────────┘
                       ▼                      ▼
              ┌─────────────────┐    ┌──────────────────┐
              │ Lokales Modell  │    │ Cloud-Modell      │
              │ (keine Kosten)  │    │ (via API-Key)    │
              │ sofort da       │    │ Groq/OpenAI/...  │
              └─────────────────┘    └──────────────────┘
```

### Analyse-Dimensionen

| Dimension | Werte | Einfluss auf Routing |
|-----------|-------|---------------------|
| **Komplexität** | niedrig / mittel / hoch | niedrig → lokal, hoch → cloud |
| **Aufgaben-Typ** | Frage / Code / Architektur / Debug / Recherche | Code+Architektur → cloud |
| **Benötigte Tools** | bash, write, edit, git, search, vision, reasoning | Reasoning/Vision → cloud |
| **Geschätzte Schritte** | 1–3 / 4–8 / 9+ | 9+ → cloud |
| **Kontext-Größe** | klein (<2K) / mittel / groß (>8K Tokens) | groß → cloud mit langem Kontext |
| **Usage-Limit** | lokal verfügbar / limitiert / erschöpft | limitiert/erschöpft → cloud |

### Router-Architektur

```
TaskAnalyzer (eigenes Python-Modul)
│
├── analyze(task: str) → TaskProfile
│   ├── complexity: Low | Medium | High
│   ├── task_type: Query | Code | Architecture | Debug | Research
│   ├── required_tools: list[str]
│   ├── estimated_steps: int
│   └── estimated_tokens: int
│
├── route(profile: TaskProfile) → ModelTarget
│   ├── model_id: str (z.B. "gemma4:12b" | "groq:llama-3.3-70b")
│   ├── adapter: str (z.B. "ollama" | "groq" | "openai")
│   └── reason: str (für UI-Anzeige)
│
├── ProviderTracker (erweitert)
│   ├── local_usage: dict[model → remaining calls]
│   ├── cloud_usage: dict[provider → remaining budget]
│   └── cooldown: dict[model → available_at]
│
└── RouterConfig (UI-konfigurierbar)
    ├── auto_route: bool (default: true)
    ├── preferred_local: str (Modell für lokale Tasks)
    ├── preferred_cloud: str (Provider für Cloud-Tasks)
    ├── max_local_steps: int (3 = bis 3 Schritte lokal)
    └── ask_before_cloud: bool (vor Cloud-Nutzung nachfragen)
```

### UI-Komponenten

| Element | Beschreibung |
|---------|-------------|
| **Routing-Indikator** | Zeigt im Chat: "🌐 Cloud" oder "💻 Lokal" neben der Antwort |
| **Config-Seite** | In Settings: Router-Konfiguration (Auto-Route, Präferenzen) |
| **Usage-Übersicht** | Dashboard: Verbrauch lokale vs. Cloud-Modelle |
| **Manuelle Überschreibung** | User kann Routing manuell überschreiben: "@cloud mach ..." oder "@lokal mach ..." |

### Priorisierung

```
P0 – Basis
├── TaskAnalyzer-Modul (Klassifikation + Routing-Logik)
├── Leichtes lokales Modell als Analyzer (glm-4.7-flash oder gemma4:2b)
├── Routing-Entscheidung vor Agent-Loop
├── ProviderTracker-Erweiterung: lokale Usage-Limits
└── Routing-Indikator in der UI

P1 – Cloud-Integration
├── Cloud-Adapter für Groq (API-Key only)
├── Automatisches Cloud-Routing bei komplexen Tasks
├── Ask-before-Cloud: User-Zustimmung vor Cloud-Nutzung
├── Usage-Dashboard (lokal vs. cloud)
└── Manuelle Überschreibung (@cloud / @lokal)

P2 – Lernen + Optimieren
├── Router lernt aus User-Feedback: "falsch geroutet"
├── Task-Template-Erkennung (wiederkehrende Tasks erkennen)
├── Batch-Routing: mehrere Subtasks parallel routen
├── Kosten-Tracking (Cloud-Ausgaben im Blick)
└── Vorschlag: "Diese Task würde ich nächstes Mal lokal machen"
```

---

## 10. Konkrete nächste Schritte (Priorisiert)

```
P0 – Muss diese Woche
├── ToolRegistry neu: StructuredTool + JSON Schema + Permission
├── Tool-Parsing von Regex auf ModelRequest.parts umstellen
├── MCP-Client-Basis (Tools von externen MCP-Servern laden)
├── Embedding + RAG (Vektor-Memory für Kontext)
├── TaskAnalyzer-Modul (Klassifikation + Routing-Logik)           ← NEU
├── Routing-Entscheidung vor Agent-Loop                            ← NEU
├── Routing-Indikator in UI                                        ← NEU
└── Modell-Download/Install via UI (Ollama pull aus Sagent heraus)

P1 – Diese/Sprint
├── Tool-Whitelist pro Chat (allow/ask/deny)
├── Batch-Execution (mehrere Tasks planen)
├── MCP-Server für Sagent-native Tools (bash, write, edit, git)
├── Vision/Multi-Modal (Bilder erkennen)
├── Chat-Verlauf verdichten (Token-Sparen)
├── Native Cloud-Adapter (Groq, OpenAI)                             ← NEU
├── Automatisches Cloud-Routing bei komplexen Tasks                 ← NEU
├── Ask-before-Cloud: User-Zustimmung vor Cloud-Nutzung             ← NEU
└── Mehrere Remote-Ollama-Instanzen parallel (Server + NAS + Local)

P2 – Nächster Sprint
├── Artefakte (Dateien aus Chat erstellen/übernehmen)
├── Multi-Agent (Sub-Agents für Code/Tests/Suche)
├── Split View (Chat + Editor)
├── Modell-Einstellungen pro Conversation
├── Dark Mode
└── Native Provider-Plugins für Groq (einfach API-Key, kein Endpoint-Gefummel)

P3 – Zukunft
├── Autonomer Modus
├── CI/CD Integration
├── Model Fine-Tuning via QLoRA
├── Audio-Input / Sprachsteuerung
├── Windows + Linux Support
└── Team-Features (mehrere User teilen Sagent-Server)
```

---

## 11. Architektur-Entscheidungen (Juli 2026)

### Lizenz: Apache 2.0 (Open Source, vollständig kostenlos)
- Schutz vor Patent-Klagen
- Kompatibel mit opencode und anderen Open-Source-Projekten
- Erlaubt kommerzielle Nutzung (aber Sagent bleibt forever free)
- Keine Paywalls, keine Premium-Features, kein Freemium

### MCP: Standard für Tool-Integration
- ToolRegistry wird auf MCP umgestellt
- Externe MCP-Server einbindbar (Community-Plugins)
- Sagent wird auch selbst MCP-Server → andere Tools (Handy, CLI, VS Code) können Sagents Fähigkeiten nutzen

### Platform: Hybrid
- Desktop-App (Electron) als Haupt-Interface
- Backend kann standalone auf Server laufen
- Web-Interface für Zugriff von anderen Geräten
- Sync/Teilen: Aufgaben an Freunde senden, Feedback einholen

### Cloud-Modelle
- Native Provider-Plugins (Groq, OpenAI, Anthropic – nur API-Key nötig)
- Custom Endpoint für Selbst-Hosting (Ollama remote, vLLM, TGI, LM Studio)

### Model-Hosting
- Ollama für lokale Entwicklung
- vLLM/TGI für Server-Betrieb (schneller, Multi-GPU, lange Kontexte)
- LM Studio als weitere Option

---

## 12. Selbst-Erweiterung (Killer-Feature)

### Vision

Sagent soll sich selbst erweitern können. Wenn ihm eine Fähigkeit fehlt (z.B. Docker-Support, eine API-Anbindung, ein neues Tool), baut er sie sich **mit dir zusammen** – direkt aus dem Chat heraus.

### Wie es funktioniert

```
User: "Analysier diesen Docker-Container"
Sagent: ─┬─ Docker-Tool vorhanden? ──→ ja → ausführen
          └─ Docker-Tool NICHT vorhanden →
             "Ich habe kein Docker-Tool. Sollen wir eins bauen?
              Ich brauche: Docker-Pfad, Socket-IP, Berechtigungen.
              Ich schreibe den Code, du prüfst und aktivierst es."
```

### Konkrete Schritte

| Phase | Was passiert |
|-------|-------------|
| **1. Erkennung** | Sagent erkennt: Task fehlgeschlagen weil Tool/Interface fehlt |
| **2. Vorschlag** | Sagent fragt: "Soll ich ein X-Tool bauen?" + schreibt Code |
| **3. Code-Review** | User sieht den Code, gibt Feedback, Sagent passt an |
| **4. Aktivierung** | Tool wird geladen (Hot-Reload via MCP), sofort nutzbar |
| **5. Lernen** | Sagent merkt sich: "Für solche Tasks brauche ich Tool X" |

### Technische Voraussetzungen

- **MCP als Plugin-System**: Neue Tools sind MCP-Server → kein Backend-Neustart nötig
- **Tool-Generator**: Sagent schreibt MCP-Server-Code (Python/TypeScript), legt ihn ab, registriert ihn
- **Sandbox**: Generierte Tools laufen isoliert, User muss aktivieren
- **Template-Bibliothek**: Fertige MCP-Vorlagen für API-Integration, Shell-Tools, Web-Scraping etc.

### Anwendungsbeispiele

| Fehlende Fähigkeit | Sagent baut |
|-------------------|-------------|
| Docker | Docker-MCP-Tool: Container list/start/stop/logs |
| API-Anbindung (z.B. Jira) | Jira-MCP-Tool: Issues lesen/erstellen |
| Datenbank (z.B. PostgreSQL) | SQL-MCP-Tool: Query-Ausführung |
| Slack/Teams | Notification-MCP-Tool: Nachrichten senden |
| Datei-Format (z.B. Excel) | xlwings/openpyxl-Tool: Tabellen lesen/schreiben |
| Browser-Automatisierung | Playwright-MCP-Tool: Seiten crawlen/interagieren |

### Priorisierung für Sagent

```
P0 – Fundament
├── MCP-Client: Externe MCP-Server laden
├── ToolRegistry: Neue Tools via Chat registrierbar
├── Selbst-Diagnose: Erkennen wenn ein Tool fehlt
├── Extensions-Seite (wie Settings, Button neben Neuer Chat)
└── Ollama-Modell-Browser: Alle installierten Modelle anzeigen + neue aus Library installieren

P1 – Tool-Generator
├── Sagent schreibt MCP-Server-Code für fehlende Tools
├── Template-Bibliothek (API, Shell, DB, Web)
├── User-Review + Approval im Chat
├── Hot-Reload: Tool sofort nutzbar ohne Neustart
└── Extensions im Chat aufrufbar (Output inline)

P2 – Selbst-Lernen
├── Sagent merkt sich wiederkehrende fehlende Fähigkeiten
├── Schlägt proaktiv Erweiterungen vor
├── Eigenen Code refactorn (Tool-Verbesserung)
└── Interface-Builder: Fehlende UI-Elemente selbst erstellen

P3 – Autonome Verbesserung
├── Sagent erkennt Ineffizienzen im eigenen Code
├── Baut und testet Verbesserungen selbstständig
├── User approved nur noch
└── Extension-Store: Self-extensions mit Community teilen
```

---

## 13. UI-Konzept

### Seiten-Struktur (aktuell + neu)

```
┌──────────┬──────────────────────────────┐
│ Sidebar  │  Hauptbereich                 │
│          │                              │
│ Neuer    │  ┌─ Chat ─────────────────┐  │
│ Chat     │  │                        │  │
│          │  │  (normaler Chat)       │  │
│ Suche    │  │                        │  │
│          │  └────────────────────────┘  │
│ Extensions│                             │
│ (Button) │  ┌─ Extensions ────────────┐ │
│          │  │  Seite wie Settings,    │ │
│ Einstell.│  │  aber für Extensions:   │ │
│          │  │  - Installierte Tools   │ │
│          │  │  - Self-built Interfaces│ │
│          │  │  - Aktivieren/Deaktiv.  │ │
│          │  │  - Daten/Output anzeigen│ │
│          │  └────────────────────────┘ │
└──────────┴──────────────────────────────┘
```

### Extensions-Seite
- **Neuer Button** in der Sidebar-Leiste, direkt unter "Neuer Chat"
- Öffnet eine **Full-Page View** (wie Settings, eigener `currentView`-State)
- Zeigt alle installierten Extensions (Tools, Interfaces, MCP-Server)
- Pro Extension:
  - Name + Beschreibung
  - Status (aktiv/inaktiv)
  - Config (API-Key, Endpoint, Parameter)
  - Output-Fenster (Daten die die Extension liefert)
  - "Im Chat öffnen" Button → wechselt zurück in Chat mit Extension-Kontext

### Chat + Extensions
- Im Chat kann der User Extensions erwähnen: `@jira zeige meine Tickets`
- Sagent ruft die Extension auf → Output erscheint **inline im Chat**
- Der Chat ist der primäre Interaktionsmodus, Extensions sind die Werkzeuge darin
- Neue Interfaces (self-built) sind einfach MCP-Tools → tauchen automatisch in der Extension-Liste auf

### Struktur

```
Extensions (Container)
├── Extension 1: "Jira Tool"
│   ├── MCP-Server (lokal)
│   ├── Config: URL + API-Key
│   └── Status: Aktiv
├── Extension 2: "Docker Manager"
│   ├── MCP-Server (lokal)
│   ├── Config: Socket-Pfad
│   └── Status: Inaktiv
└── Extension 3: "PostgreSQL"
    ├── Self-built (generiert von Sagent)
    ├── Config: Host + Port + User
    └── Status: Neu (muss aktiviert werden)
```

---

## 14. Zusammenfassung

```
Sagent = Lokaler KI-Assistent
       + Automatische Problemlösung
       + Fehlende Fähigkeiten selbst einbauen (Killer-Feature)
       + MCP-Standard für Tools + Extensions
       + Cloud-Modelle (Native Plugins + Custom)
       + Lokale Modelle (Ollama + vLLM/TGI)
       + Intelligent Task Routing (lokal analysieren, cloud lösen)
       + Desktop + Web + Server
       + Teilen mit Freunden
       + Extensions-Seite (eigene View, Button in Sidebar)
       = Dein persönlicher, wachsender KI-Entwickler
```
