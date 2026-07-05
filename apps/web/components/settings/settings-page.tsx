"use client";

import {
  Brain, Command, Gear, Keyboard, MagnifyingGlass, Palette, ArrowLeft, Plus, Trash,
} from "@phosphor-icons/react";
import { useState } from "react";

export type UserModelConfig = {
  id: string;
  label: string;
  provider: string;
  model: string;
  apiKey: string;
  endpoint: string;
};

type ThemeMode = "system" | "light" | "dark";
type SettingsTab = "general" | "appearance" | "configuration" | "shortcuts" | "models";

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
  }
}

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

  return (
    <div className="settings-card">
      <h3>Eigene Modelle</h3>
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
      {showForm ? (
        <div className="settings-model-form">
          <input className="settings-model-input" placeholder="Anzeigename" value={label} onChange={e => setLabel(e.target.value)} />
          <input className="settings-model-input" placeholder="Modellname (z.B. gemma4, qwen2.5-coder)" value={model} onChange={e => setModel(e.target.value)} />
          <input className="settings-model-input" placeholder="API-Key (optional, für Endpoints mit Auth)" type="password" value={apiKey} onChange={e => setApiKey(e.target.value)} />
          <input className="settings-model-input" placeholder="Endpoint (z.B. http://192.168.1.100:11434)" value={endpoint} onChange={e => setEndpoint(e.target.value)} />
          <div className="settings-model-form-actions">
            <button type="button" className="btn btn-primary btn-sm" onClick={handleAdd}>Hinzufügen</button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => { setShowForm(false); setLabel(""); setModel(""); setApiKey(""); setEndpoint(""); }}>Abbrechen</button>
          </div>
        </div>
      ) : (
        <button type="button" className="btn btn-ghost btn-sm settings-add-btn" onClick={() => { setShowForm(true); }}>
          <Plus weight="regular" /> Modell hinzufügen
        </button>
      )}
    </div>
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
