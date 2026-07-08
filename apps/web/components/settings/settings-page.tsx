"use client";

import {
  Brain, Command, Gear, Keyboard, MagnifyingGlass, Palette, ArrowLeft, Plus, Trash, ShieldCheck,
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";

export type UserModelConfig = {
  id: string;
  label: string;
  provider: string;
  model: string;
  apiKey: string;
  endpoint: string;
};

type ThemeMode = "system" | "light" | "dark";
type SettingsTab = "general" | "appearance" | "configuration" | "shortcuts" | "models" | "permissions";

type Props = {
  onBack: () => void;
  theme: ThemeMode;
  onSetTheme: (t: ThemeMode) => void;
  userModels: UserModelConfig[];
  onAddUserModel: (cfg: UserModelConfig) => void;
  onRemoveUserModel: (id: string) => void;
};

const tabs: { id: SettingsTab; icon: React.ElementType; label: string }[] = [
  { id: "general", icon: Gear, label: "Allgemein" },
  { id: "appearance", icon: Palette, label: "Aussehen" },
  { id: "configuration", icon: Command, label: "Konfiguration" },
  { id: "shortcuts", icon: Keyboard, label: "Tastenkürzel" },
  { id: "models", icon: Brain, label: "KI Modelle" },
  { id: "permissions", icon: ShieldCheck, label: "Berechtigungen" },
];

export function SettingsPage({ onBack, theme, onSetTheme, userModels, onAddUserModel, onRemoveUserModel }: Props) {
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [search, setSearch] = useState("");
  const [workMode, setWorkMode] = useState<"code" | "daily">("code");
  const [permDefault, setPermDefault] = useState(true);
  const [permAuto, setPermAuto] = useState(true);
  const [permFull, setPermFull] = useState(false);
  const [appTheme, setAppTheme] = useState<ThemeMode>(theme);
  const [accentColor, setAccentColor] = useState("blue");
  const [language, setLanguage] = useState("auto");
  const [defaultOpenTarget, setDefaultOpenTarget] = useState("default");
  const [showMenuBar, setShowMenuBar] = useState(true);

  const filteredTabs = search.trim()
    ? tabs.filter(t => t.label.toLowerCase().includes(search.toLowerCase()))
    : tabs;

  function handleSetTheme(t: ThemeMode) {
    setAppTheme(t);
    onSetTheme(t);
  }

  return (
    <div className="settings-fullpage">
      <aside className="settings-fullpage-sidebar">
        <button type="button" className="settings-back-btn" onClick={onBack}>
          <ArrowLeft weight="regular" />
          Zurück zur App
        </button>
        <div className="settings-search-wrap">
          <MagnifyingGlass weight="regular" className="settings-search-icon" />
          <input
            type="text"
            className="settings-search-input"
            placeholder="Einstellungen durchsuchen..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <nav className="settings-nav">
          {filteredTabs.map(tab => (
            <button
              key={tab.id}
              type="button"
              className={`settings-nav-item${activeTab === tab.id ? " active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon weight="regular" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </aside>
      <main className="settings-fullpage-content">
        <SettingsPanel
          tab={activeTab}
          theme={appTheme}
          onSetTheme={handleSetTheme}
          workMode={workMode}
          setWorkMode={setWorkMode}
          permDefault={permDefault}
          setPermDefault={setPermDefault}
          permAuto={permAuto}
          setPermAuto={setPermAuto}
          permFull={permFull}
          setPermFull={setPermFull}
          accentColor={accentColor}
          setAccentColor={setAccentColor}
          language={language}
          setLanguage={setLanguage}
          defaultOpenTarget={defaultOpenTarget}
          setDefaultOpenTarget={setDefaultOpenTarget}
          showMenuBar={showMenuBar}
          setShowMenuBar={setShowMenuBar}
          userModels={userModels}
          onAddUserModel={onAddUserModel}
          onRemoveUserModel={onRemoveUserModel}
        />
      </main>
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      className={`settings-toggle${checked ? " on" : ""}`}
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
    >
      <span className="settings-toggle-knob" />
    </button>
  );
}

type PanelProps = {
  tab: SettingsTab;
  theme: ThemeMode;
  onSetTheme: (t: ThemeMode) => void;
  workMode: "code" | "daily";
  setWorkMode: (v: "code" | "daily") => void;
  permDefault: boolean;
  setPermDefault: (v: boolean) => void;
  permAuto: boolean;
  setPermAuto: (v: boolean) => void;
  permFull: boolean;
  setPermFull: (v: boolean) => void;
  accentColor: string;
  setAccentColor: (v: string) => void;
  language: string;
  setLanguage: (v: string) => void;
  defaultOpenTarget: string;
  setDefaultOpenTarget: (v: string) => void;
  showMenuBar: boolean;
  setShowMenuBar: (v: boolean) => void;
  userModels: UserModelConfig[];
  onAddUserModel: (cfg: UserModelConfig) => void;
  onRemoveUserModel: (id: string) => void;
};

function SettingsPanel(props: PanelProps) {
  switch (props.tab) {
    case "general":
      return (
        <div className="settings-panel">
          <h2>Allgemein</h2>
          <div className="settings-card">
            <h3>Arbeitsmodus</h3>
            <div className="mode-cards">
              <button
                type="button"
                className={`mode-card${props.workMode === "code" ? " active" : ""}`}
                onClick={() => props.setWorkMode("code")}
              >
                <CodeIcon />
                <span>Zum Programmieren</span>
              </button>
              <button
                type="button"
                className={`mode-card${props.workMode === "daily" ? " active" : ""}`}
                onClick={() => props.setWorkMode("daily")}
              >
                <BriefcaseIcon />
                <span>Für die tägliche Arbeit</span>
              </button>
            </div>
          </div>
          <div className="settings-card">
            <h3>Berechtigungen</h3>
            <SettingsRow label="Standardberechtigungen" hint="Standard-Sicherheitsrichtlinie verwenden">
              <Toggle checked={props.permDefault} onChange={props.setPermDefault} />
            </SettingsRow>
            <SettingsRow label="Automatische Überprüfung" hint="Aktionen vor Ausführung prüfen">
              <Toggle checked={props.permAuto} onChange={props.setPermAuto} />
            </SettingsRow>
            <SettingsRow label="Vollzugriff" hint="Alle Aktionen ohne Rückfrage erlauben">
              <Toggle checked={props.permFull} onChange={props.setPermFull} />
            </SettingsRow>
          </div>
        </div>
      );

    case "appearance":
      return (
        <div className="settings-panel">
          <h2>Aussehen</h2>
          <div className="settings-card">
            <h3>Theme</h3>
            <div className="theme-selector">
              {([["system", "System"], ["light", "Hell"], ["dark", "Dunkel"]] as const).map(([val, label]) => (
                <button
                  key={val}
                  type="button"
                  className={`theme-option${props.theme === val ? " active" : ""}`}
                  onClick={() => props.onSetTheme(val)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="settings-card">
            <h3>Akzentfarbe</h3>
            <div className="accent-colors">
              {["blue", "green", "purple", "orange"].map(c => (
                <button
                  key={c}
                  type="button"
                  className={`accent-swatch${props.accentColor === c ? " active" : ""}`}
                  style={{ backgroundColor: c === "blue" ? "#3b82f6" : c === "green" ? "#22c55e" : c === "purple" ? "#a855f7" : "#f97316" }}
                  onClick={() => props.setAccentColor(c)}
                  aria-label={c}
                />
              ))}
            </div>
          </div>
        </div>
      );

    case "configuration":
      return (
        <div className="settings-panel">
          <h2>Konfiguration</h2>
          <div className="settings-card">
            <h3>Sprache</h3>
            <select className="settings-select" value={props.language} onChange={e => props.setLanguage(e.target.value)}>
              <option value="auto">Automatisch erkennen</option>
              <option value="de">Deutsch</option>
              <option value="en">English</option>
            </select>
          </div>
          <div className="settings-card">
            <h3>Standardziel zum Öffnen von Dateien</h3>
            <select className="settings-select" value={props.defaultOpenTarget} onChange={e => props.setDefaultOpenTarget(e.target.value)}>
              <option value="default">Default app</option>
              <option value="vscode">VS Code</option>
              <option value="cursor">Cursor</option>
            </select>
          </div>
          <div className="settings-card">
            <SettingsRow label="In Menüleiste anzeigen" hint="Symbol in der Menüleiste anzeigen">
              <Toggle checked={props.showMenuBar} onChange={props.setShowMenuBar} />
            </SettingsRow>
          </div>
        </div>
      );

    case "shortcuts":
      return (
        <div className="settings-panel">
          <h2>Tastenkürzel</h2>
          <div className="settings-card">
            <table className="shortcuts-table">
              <tbody>
                <tr><td><kbd>⌘</kbd> <kbd>N</kbd></td><td>Neuer Chat</td></tr>
                <tr><td><kbd>⌘</kbd> <kbd>K</kbd></td><td>Suche öffnen</td></tr>
                <tr><td><kbd>⌘</kbd> <kbd>,</kbd></td><td>Einstellungen öffnen</td></tr>
                <tr><td><kbd>Enter</kbd></td><td>Chat senden</td></tr>
                <tr><td><kbd>Shift</kbd> <kbd>Enter</kbd></td><td>Neue Zeile</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      );

    case "models":
      return (
        <div className="settings-panel">
          <h2>KI Modelle</h2>
          <ModelsSection
            userModels={props.userModels}
            onAddUserModel={props.onAddUserModel}
            onRemoveUserModel={props.onRemoveUserModel}
          />
        </div>
      );

    case "permissions":
      return <ToolPermissionsSection />;
  }
}

const PROVIDER_PRESETS: { id: string; label: string; endpoint: string; models: string[] }[] = [
  { id: "groq", label: "Groq", endpoint: "https://api.groq.com", models: ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"] },
  { id: "openai", label: "OpenAI", endpoint: "https://api.openai.com", models: ["gpt-4o", "gpt-4o-mini", "o3-mini", "o4-mini"] },
  { id: "anthropic", label: "Anthropic", endpoint: "https://api.anthropic.com", models: ["claude-sonnet-4-20250514", "claude-haiku-3-5-sonnet-20241022"] },
  { id: "google", label: "Google Gemini", endpoint: "https://generativelanguage.googleapis.com", models: ["gemini-2.5-flash", "gemini-2.5-pro"] },
  { id: "together", label: "Together AI", endpoint: "https://api.together.xyz", models: ["mistralai/Mixtral-8x7B-Instruct-v0.1", "Qwen/Qwen2.5-72B-Instruct"] },
];

function ModelsSection({ userModels, onAddUserModel, onRemoveUserModel }: {
  userModels: UserModelConfig[];
  onAddUserModel: (cfg: UserModelConfig) => void;
  onRemoveUserModel: (id: string) => void;
}) {
  const [showForm, setShowForm] = useState(false);
  const [label, setLabel] = useState("");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [showPresets, setShowPresets] = useState(false);

  const [quickProvider, setQuickProvider] = useState("");
  const [quickKey, setQuickKey] = useState("");
  const [quickModels, setQuickModels] = useState<string[]>([]);
  const [quickSelected, setQuickSelected] = useState<Set<string>>(new Set());

  const [library, setLibrary] = useState<ModelLibEntry[]>([]);
  const [installed, setInstalled] = useState<string[]>([]);
  const [libLoading, setLibLoading] = useState(true);
  const [pulling, setPulling] = useState<Record<string, boolean>>({});
  const [customPull, setCustomPull] = useState("");
  const [pullError, setPullError] = useState("");

  // Remote Ollama state
  const [ollamaUrl, setOllamaUrl] = useState("");
  const [ollamaProbing, setOllamaProbing] = useState(false);
  const [ollamaProbeResult, setOllamaProbeResult] = useState<{name: string; size: number}[] | null>(null);
  const [ollamaProbeError, setOllamaProbeError] = useState("");
  const [ollamaSelected, setOllamaSelected] = useState<Set<string>>(new Set());
  const [ollamaLabel, setOllamaLabel] = useState("");

  useEffect(() => { loadLibrary(); }, []);

  async function loadLibrary() {
    setLibLoading(true);
    try {
      const [libR, modelsR] = await Promise.all([
        fetch(`${PERM_API}/models/library`),
        fetch(`${PERM_API}/models`),
      ]);
      if (libR.ok) {
        const data = await libR.json();
        setLibrary(data.models || []);
      }
      if (modelsR.ok) {
        const data = await modelsR.json();
        setInstalled(data
          .filter((m: {transport: string}) => m.transport !== "remote_http")
          .map((m: {model: string}) => m.model)
        );
      }
    } catch { /* backend offline */ }
    finally { setLibLoading(false); }
  }

  async function handlePull(name: string) {
    setPulling(prev => ({ ...prev, [name]: true }));
    setPullError("");
    try {
      const r = await fetch(`${PERM_API}/models/pull`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!r.ok) {
        const err = await r.text();
        setPullError(err.slice(0, 200));
      }
    } catch (e) {
      setPullError(String(e));
    }
    setTimeout(() => loadLibrary(), 1000);
  }

  function handleAdd() {
    if (!label.trim() || !model.trim()) return;
    onAddUserModel({
      id: Date.now().toString(36),
      label: label.trim(),
      provider: "custom",
      model: model.trim(),
      apiKey: apiKey.trim(),
      endpoint: endpoint.trim(),
    });
    setLabel(""); setModel(""); setApiKey(""); setEndpoint("");
    setShowForm(false);
  }

  async function handleProbeOllama() {
    if (!ollamaUrl.trim()) return;
    setOllamaProbing(true);
    setOllamaProbeError("");
    setOllamaProbeResult(null);
    setOllamaSelected(new Set());
    try {
      const r = await fetch(`${PERM_API}/ollama/probe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ base_url: ollamaUrl.trim() }),
      });
      const data = await r.json();
      if (data.error) {
        setOllamaProbeError(data.error);
      } else {
        setOllamaProbeResult(data.models || []);
        if (data.models?.length > 0) {
          setOllamaLabel(ollamaUrl.trim().replace(/^https?:\/\//, "").replace(/:11434$/, ""));
        }
      }
    } catch (e) {
      setOllamaProbeError(String(e));
    }
    setOllamaProbing(false);
  }

  function handleAddRemoteOllamaModels() {
    if (!ollamaProbeResult || ollamaSelected.size === 0) return;
    const baseLabel = ollamaLabel || ollamaUrl.trim().replace(/^https?:\/\//, "").replace(/:11434$/, "");
    for (const m of ollamaProbeResult) {
      if (ollamaSelected.has(m.name)) {
        onAddUserModel({
          id: "ollama-" + m.name.replace(/[:\/.]/g, "-") + "-" + Date.now().toString(36),
          label: `${baseLabel} – ${m.name}`,
          provider: "ollama-remote",
          model: m.name,
          apiKey: "",
          endpoint: ollamaUrl.trim(),
        });
      }
    }
    setOllamaProbeResult(null);
    setOllamaUrl("");
    setOllamaLabel("");
    setOllamaSelected(new Set());
  }

  function toggleOllamaModel(name: string) {
    setOllamaSelected(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  const categories = [...new Set(library.map(m => m.category))];

  return (
    <>
      <div className="settings-card">
        <h3>Eigene Modelle (Cloud / Remote)</h3>
        {userModels.length === 0 ? (
          <p className="settings-empty">Noch keine Modelle konfiguriert.</p>
        ) : (
          <ul className="settings-model-list">
            {userModels.map(m => (
              <li key={m.id} className="settings-model-item">
                <div>
                  <span className="settings-model-name">{m.label}</span>
                  <span className="settings-model-desc">{m.model}{m.endpoint ? ` · ${m.endpoint}` : ""}</span>
                </div>
                <button type="button" className="settings-model-remove" onClick={() => onRemoveUserModel(m.id)} aria-label="Entfernen">
                  <Trash weight="regular" />
                </button>
              </li>
            ))}
          </ul>
        )}
        <div style={{ marginBottom: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <div className="settings-card" style={{ background: "var(--surface2)" }}>
            <h4 style={{ margin: "0 0 8px", fontSize: 14 }}>Schnell-Konfiguration</h4>
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end", flexWrap: "wrap" }}>
              <div className="form-field" style={{ flex: "0 0 auto", marginBottom: 0 }}>
                <label className="form-label">Anbieter</label>
                <select className="form-input" value={quickProvider} onChange={e => {
                  const p = e.target.value;
                  setQuickProvider(p);
                  const preset = PROVIDER_PRESETS.find(pp => pp.id === p);
                  if (preset) {
                    setQuickKey("");
                    setQuickModels(preset.models);
                    setQuickSelected(new Set(preset.models));
                  }
                }}>
                  <option value="">– Auswählen –</option>
                  {PROVIDER_PRESETS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                </select>
              </div>
              <div className="form-field" style={{ flex: 1, marginBottom: 0 }}>
                <label className="form-label">API-Key</label>
                <input className="form-input" type="password" value={quickKey} onChange={e => setQuickKey(e.target.value)}
                  placeholder={quickProvider ? "sk-..." : "Zuerst Anbieter wählen"} disabled={!quickProvider} />
              </div>
              <button type="button" className="btn btn-primary btn-sm"
                disabled={!quickProvider || !quickKey || quickSelected.size === 0}
                onClick={() => {
                  const preset = PROVIDER_PRESETS.find(p => p.id === quickProvider);
                  if (!preset) return;
                  for (const m of preset.models) {
                    if (quickSelected.has(m)) {
                      onAddUserModel({
                        id: `${quickProvider}-${m.replace(/[:\/.]/g, "-")}-${Date.now().toString(36)}`,
                        label: `${preset.label} – ${m}`,
                        provider: quickProvider,
                        model: m,
                        apiKey: quickKey.trim(),
                        endpoint: preset.endpoint,
                      });
                    }
                  }
                  setQuickKey("");
                }}>
                <Plus weight="bold" /> {quickSelected.size === quickModels.length ? "Alle hinzufügen" : `${quickSelected.size} Modell(e) hinzufügen`}
              </button>
            </div>
            {quickModels.length > 0 && (
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
                {quickModels.map(m => (
                  <label key={m} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, cursor: "pointer" }}>
                    <input type="checkbox" checked={quickSelected.has(m)}
                      onChange={() => setQuickSelected(prev => { const n = new Set(prev); n.has(m) ? n.delete(m) : n.add(m); return n; })} />
                    {m}
                  </label>
                ))}
              </div>
            )}
          </div>
        </div>
        {showForm ? (
          <div className="settings-model-form">
            {!showPresets ? (
              <button type="button" className="btn btn-ghost btn-sm" style={{ marginBottom: 8 }} onClick={() => setShowPresets(true)}>
                Provider-Voreinstellungen anzeigen
              </button>
            ) : (
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
                  {PROVIDER_PRESETS.map(p => (
                    <button
                      key={p.id}
                      type="button"
                      className={`btn btn-sm ${endpoint === p.endpoint ? "btn-primary" : "btn-ghost"}`}
                      onClick={() => {
                        setEndpoint(p.endpoint);
                        setLabel(p.label);
                        setModel(p.models[0]);
                      }}
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
                {endpoint && (() => {
                  const preset = PROVIDER_PRESETS.find(p => p.endpoint === endpoint);
                  if (!preset) return null;
                  return (
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
                      {preset.models.map(m => (
                        <button
                          key={m}
                          type="button"
                          className={`btn btn-sm ${model === m ? "btn-primary" : "btn-ghost"}`}
                          onClick={() => setModel(m)}
                        >
                          {m}
                        </button>
                      ))}
                    </div>
                  );
                })()}
              </div>
            )}
            <input className="settings-model-input" placeholder="Anzeigename" value={label} onChange={e => setLabel(e.target.value)} />
            <input className="settings-model-input" placeholder="Modellname (z.B. gpt-4o)" value={model} onChange={e => setModel(e.target.value)} />
            <input className="settings-model-input" placeholder="API-Key" type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} />
            <input className="settings-model-input" placeholder="Endpoint (z.B. https://api.groq.com)" value={endpoint} onChange={e => setEndpoint(e.target.value)} />
            <div className="settings-model-form-actions">
              <button type="button" className="btn btn-primary btn-sm" onClick={handleAdd}>Hinzufügen</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => { setShowForm(false); setShowPresets(false); setLabel(""); setModel(""); setApiKey(""); setEndpoint(""); }}>Abbrechen</button>
            </div>
          </div>
        ) : (
          <button type="button" className="btn btn-ghost btn-sm settings-add-btn" onClick={() => { setShowForm(true); }}>
            <Plus weight="regular" /> Cloud-Modell hinzufügen
          </button>
        )}
      </div>

      <div className="settings-card">
        <h3>Remote-Ollama-Instanzen</h3>
        <p style={{ fontSize: 13, opacity: 0.6, margin: "4px 0 12px" }}>
          Füge entfernte Ollama-Server hinzu (z.B. <code>http://192.168.1.100:11434</code>).
          Modelle werden automatisch erkannt und als eigene Modelle hinzugefügt.
        </p>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input
            className="form-input"
            value={ollamaUrl}
            onChange={e => setOllamaUrl(e.target.value)}
            placeholder="http://192.168.1.100:11434"
            style={{ flex: 1 }}
          />
          <button
            type="button"
            className="btn btn-primary btn-sm"
            disabled={!ollamaUrl.trim() || ollamaProbing}
            onClick={handleProbeOllama}
          >
            {ollamaProbing ? "Suche…" : "Erkunden"}
          </button>
        </div>
        {ollamaProbeError && (
          <div style={{ fontSize: 13, color: "#ef4444", marginBottom: 8 }}>{ollamaProbeError}</div>
        )}
        {ollamaProbeResult && ollamaProbeResult.length === 0 && (
          <p style={{ fontSize: 13, opacity: 0.6 }}>Keine Modelle auf diesem Server gefunden.</p>
        )}
        {ollamaProbeResult && ollamaProbeResult.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <div style={{ display: "flex", gap: 4, alignItems: "center", marginBottom: 6 }}>
              <input
                className="form-input"
                value={ollamaLabel}
                onChange={e => setOllamaLabel(e.target.value)}
                placeholder="Anzeigename für diese Instanz"
                style={{ flex: 1, fontSize: 12 }}
              />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 200, overflowY: "auto" }}>
              {ollamaProbeResult.map(m => (
                <label key={m.name} className="perm-tool-row" style={{ cursor: "pointer", padding: "4px 0" }}>
                  <input
                    type="checkbox"
                    checked={ollamaSelected.has(m.name)}
                    onChange={() => toggleOllamaModel(m.name)}
                    style={{ marginRight: 8 }}
                  />
                  <div style={{ flex: 1 }}>
                    <strong style={{ fontSize: 13 }}>{m.name}</strong>
                    {m.size > 0 && (
                      <span style={{ fontSize: 11, opacity: 0.5, marginLeft: 8 }}>
                        {m.size > 1_000_000_000 ? `${(m.size / 1_000_000_000).toFixed(1)} GB` : `${(m.size / 1_000_000).toFixed(0)} MB`}
                      </span>
                    )}
                  </div>
                </label>
              ))}
            </div>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              disabled={ollamaSelected.size === 0}
              onClick={handleAddRemoteOllamaModels}
              style={{ marginTop: 8 }}
            >
              {ollamaSelected.size} Modell{ollamaSelected.size !== 1 ? "e" : ""} hinzufügen
            </button>
          </div>
        )}
      </div>

      <div className="settings-card">
        <h3>Lokale Modelle verwalten (Ollama)</h3>

        {libLoading ? (
          <p className="settings-empty">Lade Modell-Bibliothek…</p>
        ) : (
          <>
            <p style={{ fontSize: 13, opacity: 0.6, margin: "4px 0 12px" }}>
              {installed.length} Modell{installed.length !== 1 ? "e" : ""} installiert.
            </p>

            {pullError && (
              <div style={{ fontSize: 13, color: "#ef4444", marginBottom: 12 }}>{pullError}</div>
            )}

            {categories.map(cat => (
              <div key={cat} style={{ marginBottom: 16 }}>
                <h4 style={{ fontSize: 13, textTransform: "capitalize", margin: "8px 0 4px", opacity: 0.7 }}>
                  {cat === "tools" ? "⚙ Werkzeug-Modelle" : cat === "embedding" ? "📐 Embedding" : cat === "vision" ? "👁 Vision" : cat === "thinking" ? "🧠 Reasoning" : cat}
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {library.filter(m => m.category === cat).map(m => (
                    <div key={m.name} className="perm-tool-row" style={{ padding: "8px 0" }}>
                      <div style={{ flex: 1 }}>
                        <strong style={{ fontSize: 13 }}>{m.name}</strong>
                        <span style={{ fontSize: 11, opacity: 0.5, marginLeft: 8 }}>{m.size}</span>
                        <div style={{ fontSize: 11, opacity: 0.6, marginTop: 2 }}>{m.description}</div>
                      </div>
                      {m.installed || installed.includes(m.name) ? (
                        <span style={{ fontSize: 12, color: "#22c55e", whiteSpace: "nowrap" }}>✓ Installiert</span>
                      ) : (
                        <button
                          type="button"
                          className="btn btn-primary btn-sm"
                          disabled={pulling[m.name]}
                          onClick={() => handlePull(m.name)}
                          style={{ whiteSpace: "nowrap" }}
                        >
                          {pulling[m.name] ? "Lädt…" : "Installieren"}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 8 }}>
              <h4 style={{ fontSize: 13, margin: "0 0 8px", opacity: 0.7 }}>Benutzerdefinierter Pull</h4>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  className="form-input"
                  value={customPull}
                  onChange={e => setCustomPull(e.target.value)}
                  placeholder="z.B. llama3.2:3b, deepseek-r1:8b"
                  style={{ flex: 1 }}
                />
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  disabled={!customPull.trim() || pulling[customPull.trim()]}
                  onClick={() => { if (customPull.trim()) handlePull(customPull.trim()); }}
                >
                  Pull
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function SettingsRow({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="settings-row">
      <div>
        <span className="settings-row-label">{label}</span>
        {hint && <span className="settings-row-hint">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

type ToolPermInfo = { name: string; permission: "allow" | "ask" | "deny" };
type ModelLibEntry = { name: string; description: string; size: string; category: string; installed: boolean };

const PERM_API = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8765";

function ToolPermissionsSection() {
  const [tools, setTools] = useState<ToolPermInfo[]>([]);
  const [defaultPerm, setDefaultPerm] = useState<"allow" | "ask" | "deny">("allow");
  const [loading, setLoading] = useState(true);
  const [dirty, setDirty] = useState(false);

  useEffect(() => { loadPermissions(); }, []);

  async function loadPermissions() {
    try {
      const r = await fetch(`${PERM_API}/tools/permissions`);
      if (!r.ok) return;
      const data = await r.json();
      setDefaultPerm(data.default);
      setTools(data.tools);
    } catch { /* backend offline */ }
    finally { setLoading(false); }
  }

  async function savePermissions() {
    const overrides: Record<string, string> = {};
    for (const t of tools) {
      if (t.permission !== defaultPerm) {
        overrides[t.name] = t.permission;
      }
    }
    try {
      await fetch(`${PERM_API}/tools/permissions`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ default: defaultPerm, overrides }),
      });
      setDirty(false);
    } catch { /* ignore */ }
  }

  function setToolPerm(name: string, perm: "allow" | "ask" | "deny") {
    setTools(prev => prev.map(t => t.name === name ? { ...t, permission: perm } : t));
    setDirty(true);
  }

  if (loading) return <div className="settings-panel"><h2>Berechtigungen</h2><p className="settings-empty">Lade Werkzeuge…</p></div>;

  return (
    <div className="settings-panel">
      <h2>Berechtigungen</h2>

      <div className="settings-card">
        <h3>Standardberechtigung</h3>
        <p style={{ fontSize: 13, opacity: 0.6, margin: "4px 0 12px" }}>
          Greift für alle Werkzeuge, die nicht explizit überschrieben sind.
        </p>
        <div className="perm-selector">
          {(["allow", "ask", "deny"] as const).map(p => (
            <button
              key={p}
              type="button"
              className={`perm-btn${defaultPerm === p ? " active" : ""}`}
              onClick={() => { setDefaultPerm(p); setDirty(true); }}
            >
              {p === "allow" ? "✔ Erlauben" : p === "ask" ? "❓ Nachfragen" : "✖ Sperren"}
            </button>
          ))}
        </div>
      </div>

      <div className="settings-card">
        <h3>Werkzeug-Übersicht</h3>
        {tools.length === 0 ? (
          <p className="settings-empty">Keine Werkzeuge verfügbar.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {tools.map(t => (
              <div key={t.name} className="perm-tool-row">
                <div>
                  <strong style={{ fontSize: 14 }}>{t.name}</strong>
                </div>
                <select
                  className="settings-select"
                  value={t.permission}
                  onChange={e => setToolPerm(t.name, e.target.value as "allow" | "ask" | "deny")}
                  style={{ width: 140, fontSize: 13 }}
                >
                  <option value="allow">✔ Erlauben</option>
                  <option value="ask">❓ Nachfragen</option>
                  <option value="deny">✖ Sperren</option>
                </select>
              </div>
            ))}
          </div>
        )}
      </div>

      {dirty && (
        <div className="settings-card" style={{ textAlign: "center" }}>
          <button type="button" className="btn btn-primary btn-sm" onClick={savePermissions}>
            Änderungen speichern
          </button>
        </div>
      )}
    </div>
  );
}


function CodeIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  );
}

function BriefcaseIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  );
}
