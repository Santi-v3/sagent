"use client";

import { ArrowLeft, Plus, Trash, PuzzlePiece, Code, CheckCircle, XCircle, Warning, Lightbulb, Brain, FileCode } from "@phosphor-icons/react";
import { useCallback, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_AGENT_API_URL || "http://127.0.0.1:8765";

type ToolTemplate = {
  id: string;
  name: string;
  category: string;
  description: string;
};

type InstalledTool = {
  name: string;
  file: string;
  description: string;
};

type Suggestion = {
  id: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  command: string | null;
  created_at: string;
  dismissed: boolean;
};

type ToolPermission = {
  name: string;
  permission: string;
  default_permission: string;
};

function fallbackPreview(name: string, desc: string, templateId: string): string {
  const safeName = name.replace(/[^a-zA-Z0-9_]/g, "_");
  const toolDesc = desc || "Ein benutzerdefiniertes Sagent-Werkzeug";
  return `#!/usr/bin/env python3
\"\"\"
${toolDesc}

Installiert als: ${safeName}
Vorlage: ${templateId || "KI-generiert"}
\"\"\"

import subprocess
import sys
from typing import Optional


def run_tool(args: list[str]) -> Optional[str]:
    """
    Hauptfunktion des Werkzeugs.
    Wird von Sagent aufgerufen, wenn das Tool ausgeführt wird.
    """
    # TODO: Implementiere die Tool-Logik hier
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout or result.stderr


if __name__ == "__main__":
    result = run_tool(sys.argv[1:])
    if result:
        print(result)
`;
}

export function ExtensionsPage({ onBack }: { onBack: () => void }) {
  const [templates, setTemplates] = useState<ToolTemplate[]>([]);
  const [installed, setInstalled] = useState<InstalledTool[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [permissions, setPermissions] = useState<ToolPermission[]>([]);
  const [scanning, setScanning] = useState(false);
  const [lastScan, setLastScan] = useState<string | null>(null);
  const [installName, setInstallName] = useState("");
  const [installDesc, setInstallDesc] = useState("");
  const [installTemplate, setInstallTemplate] = useState<string>("");
  const [installStatus, setInstallStatus] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"tools" | "templates" | "permissions" | "suggestions">("tools");
  const [useLLM, setUseLLM] = useState(false);
  const [showCodeModal, setShowCodeModal] = useState(false);
  const [previewCode, setPreviewCode] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [pendingInstallName, setPendingInstallName] = useState("");

  const fetchAll = useCallback(async () => {
    try {
      const [tmpl, inst, sugg, perm] = await Promise.all([
        fetch(`${API_URL}/tools/templates`).then(r => r.ok ? r.json() : []),
        fetch(`${API_URL}/tools/installed`).then(r => r.ok ? r.json() : []),
        fetch(`${API_URL}/autonomous/suggestions`).then(r => r.ok ? r.json() : []),
        fetch(`${API_URL}/tools/permissions`).then(r => r.ok ? r.json() : []),
      ]);
      setTemplates(tmpl);
      setInstalled(inst);
      setSuggestions(sugg);
      setPermissions(perm);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const installFromTemplate = useCallback(async () => {
    if (!installName.trim()) return;
    setInstallStatus("installiere...");
    try {
      const res = await fetch(`${API_URL}/tools/install`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: installName.trim(),
          description: installDesc.trim(),
          template_id: installTemplate || undefined,
          use_llm: useLLM,
        }),
      });
      if (!res.ok) { setInstallStatus("Fehler: " + (await res.text())); return; }
      setInstallStatus("erfolgreich installiert");
      setInstallName(""); setInstallDesc(""); setInstallTemplate("");
      await fetchAll();
      setTimeout(() => setInstallStatus(null), 3000);
    } catch { setInstallStatus("Netzwerkfehler"); }
  }, [installName, installDesc, installTemplate, useLLM, fetchAll]);

  const uninstallTool = useCallback(async (name: string) => {
    try {
      await fetch(`${API_URL}/tools/installed/${encodeURIComponent(name)}`, { method: "DELETE" });
      await fetchAll();
    } catch { /* ignore */ }
  }, [fetchAll]);

  const dismissSuggestion = useCallback(async (id: string) => {
    try {
      await fetch(`${API_URL}/autonomous/dismiss/${id}`, { method: "POST" });
      setSuggestions(prev => prev.filter(s => s.id !== id));
    } catch { /* ignore */ }
  }, []);

  const dismissAll = useCallback(async () => {
    try {
      await fetch(`${API_URL}/autonomous/dismiss-all`, { method: "POST" });
      setSuggestions([]);
    } catch { /* ignore */ }
  }, []);

  const generatePreview = useCallback(async (name: string, desc: string, templateId: string) => {
    setPreviewLoading(true);
    setPreviewCode("");
    try {
      const res = await fetch(`${API_URL}/tools/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          description: desc.trim(),
          template_id: templateId || undefined,
          use_llm: useLLM,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPreviewCode(data.code || data.content || "// Kein Code generiert");
      } else {
        setPreviewCode(fallbackPreview(name, desc, templateId));
      }
    } catch {
      setPreviewCode(fallbackPreview(name, desc, templateId));
    }
    setPreviewLoading(false);
    setShowCodeModal(true);
    setPendingInstallName(name);
  }, [useLLM]);

  const confirmInstall = useCallback(async () => {
    setShowCodeModal(false);
    await installFromTemplate();
  }, [installFromTemplate]);

  const cancelInstall = useCallback(() => {
    setShowCodeModal(false);
    setPreviewCode("");
    setPendingInstallName("");
  }, []);

  const runScan = useCallback(async () => {
    setScanning(true);
    try {
      const res = await fetch(`${API_URL}/autonomous/scan`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setLastScan(data.timestamp);
      }
      await fetchAll();
    } catch { /* ignore */ }
    setScanning(false);
  }, [fetchAll]);

  const setToolPermission = useCallback(async (toolName: string, permission: string) => {
    try {
      const current = permissions.find(p => p.name === toolName);
      const updates = permissions.map(p => ({
        name: p.name,
        permission: p.name === toolName ? permission : p.permission,
      }));
      await fetch(`${API_URL}/tools/permissions`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ permissions: updates }),
      });
      await fetchAll();
    } catch { /* ignore */ }
  }, [permissions, fetchAll]);

  return (
    <div className="settings-fullpage">
      <div className="settings-header">
        <button type="button" className="btn btn-ghost btn-icon" onClick={onBack} aria-label="Zurück">
          <ArrowLeft weight="bold" aria-hidden="true" />
        </button>
        <h2>Extensions</h2>
      </div>

      <div className="settings-body">
        <div className="settings-section">
          <div className="settings-section-header" style={{ gap: 8 }}>
            <button className={`btn btn-sm ${activeTab === "tools" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setActiveTab("tools")}>Werkzeuge</button>
            <button className={`btn btn-sm ${activeTab === "templates" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setActiveTab("templates")}>Vorlagen</button>
            <button className={`btn btn-sm ${activeTab === "suggestions" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setActiveTab("suggestions")}>Empfehlungen{suggestions.length > 0 ? ` (${suggestions.length})` : ""}</button>
            <button className={`btn btn-sm ${activeTab === "permissions" ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setActiveTab("permissions")}>Berechtigungen</button>
          </div>
        </div>

        {activeTab === "tools" && (
          <div className="settings-section">
            <div className="settings-section-header">
              <h3>Installierte Werkzeuge</h3>
              <button type="button" className="btn btn-primary btn-sm" onClick={runScan} disabled={scanning}>
                {scanning ? "Scanne..." : "Scan ausführen"}
              </button>
            </div>

            {installed.length === 0 ? (
              <div className="settings-card" style={{ textAlign: "center", padding: 32 }}>
                <PuzzlePiece size={48} weight="thin" style={{ opacity: 0.3, marginBottom: 12 }} />
                <p style={{ margin: 0, opacity: 0.6 }}>Keine benutzerdefinierten Werkzeuge installiert.</p>
                <p style={{ margin: "4px 0 0", opacity: 0.4, fontSize: 13 }}>
                  Erstelle ein neues Werkzeug über den Vorlagen-Tab.
                </p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {installed.map(tool => (
                  <div key={tool.name} className="settings-card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div>
                      <strong><Code size={16} style={{ verticalAlign: "middle", marginRight: 6 }} />{tool.name}</strong>
                      {tool.description && <div style={{ fontSize: 12, opacity: 0.6 }}>{tool.description}</div>}
                      <div style={{ fontSize: 11, opacity: 0.4 }}>{tool.file}</div>
                    </div>
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => uninstallTool(tool.name)} title="Deinstallieren">
                      <Trash weight="regular" size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "templates" && (
          <div className="settings-section">
            <div className="settings-section-header">
              <h3>Werkzeug-Vorlagen</h3>
            </div>

            <div className="settings-card" style={{ marginBottom: 16 }}>
              <h4 style={{ marginTop: 0 }}>Neues Werkzeug installieren</h4>
              <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                <div className="form-field" style={{ flex: 1, marginBottom: 0 }}>
                  <label className="form-label">Name</label>
                  <input className="form-input" value={installName} onChange={e => setInstallName(e.target.value)}
                    placeholder="z.B. docker_tool" />
                </div>
                <div className="form-field" style={{ flex: 2, marginBottom: 0 }}>
                  <label className="form-label">Beschreibung</label>
                  <input className="form-input" value={installDesc} onChange={e => setInstallDesc(e.target.value)}
                    placeholder="Kurze Beschreibung der Funktionalität" />
                </div>
              </div>
              <div className="form-field" style={{ marginBottom: 8 }}>
                <label className="form-label">Vorlage (optional)</label>
                <select className="form-input" value={installTemplate} onChange={e => setInstallTemplate(e.target.value)}>
                  <option value="">-- Keine Vorlage (KI-generiert) --</option>
                  {templates.map(t => (
                    <option key={t.id} value={t.id}>{t.name} ({t.category})</option>
                  ))}
                </select>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
                <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 13, cursor: "pointer" }}>
                  <input type="checkbox" checked={useLLM} onChange={e => setUseLLM(e.target.checked)} />
                  KI-generierten Code verwenden (empfohlen)
                </label>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button type="button" className="btn btn-primary btn-sm" onClick={installFromTemplate} disabled={!installName.trim()}>
                  <Plus weight="bold" size={16} /> Installieren
                </button>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => generatePreview(installName, installDesc, installTemplate)}
                  disabled={!installName.trim() || previewLoading}>
                  <FileCode weight="regular" size={16} /> Code anzeigen
                </button>
                {installStatus && (
                  <span style={{ fontSize: 13, alignSelf: "center", color: installStatus.includes("erfolgreich") ? "var(--success)" : "var(--danger)" }}>
                    {installStatus}
                  </span>
                )}
              </div>
            </div>

            <h4 style={{ marginBottom: 8 }}>Verfügbare Vorlagen</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {templates.map(t => (
                <div key={t.id} className="settings-card">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <strong>{t.name}</strong>
                      <span style={{ fontSize: 11, opacity: 0.5, marginLeft: 8 }}>{t.category}</span>
                      <div style={{ fontSize: 13, opacity: 0.7, marginTop: 4 }}>{t.description}</div>
                    </div>
                    <button type="button" className="btn btn-ghost btn-sm"
                      onClick={() => { setInstallTemplate(t.id); setInstallName(t.name.toLowerCase().replace(/\s+/g, "_")); setInstallDesc(t.description); }}>
                      Verwenden
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "suggestions" && (
          <div className="settings-section">
            <div className="settings-section-header">
              <h3>Empfehlungen & Vorschläge</h3>
              {suggestions.length > 0 && (
                <button type="button" className="btn btn-ghost btn-sm" onClick={dismissAll}>Alle verwerfen</button>
              )}
            </div>

            {suggestions.length === 0 ? (
              <div className="settings-card" style={{ textAlign: "center", padding: 24 }}>
                <Lightbulb size={36} weight="thin" style={{ opacity: 0.3, marginBottom: 8 }} />
                <p style={{ margin: 0, opacity: 0.6 }}>Keine offenen Empfehlungen.</p>
                <p style={{ margin: "4px 0 0", opacity: 0.4, fontSize: 13 }}>
                  Führe einen Scan durch, um Verbesserungsvorschläge zu erhalten.
                </p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {suggestions.map(s => (
                  <div key={s.id} className="settings-card">
                    <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                      {s.severity === "critical" ? <Warning size={20} color="var(--danger)" />
                        : s.severity === "warning" ? <Warning size={20} color="var(--warning)" />
                        : <Brain size={20} color="var(--accent)" />}
                      <div style={{ flex: 1 }}>
                        <strong>{s.title}</strong>
                        <div style={{ fontSize: 13, opacity: 0.7, marginTop: 2 }}>{s.description}</div>
                        {s.command && (
                          <div style={{ fontSize: 12, opacity: 0.5, marginTop: 4, fontFamily: "monospace" }}>
                            {s.command}
                          </div>
                        )}
                        <div style={{ fontSize: 11, opacity: 0.4, marginTop: 2 }}>{s.type} – {new Date(s.created_at).toLocaleString()}</div>
                      </div>
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => dismissSuggestion(s.id)} title="Verwerfen">
                        <XCircle weight="regular" size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ marginTop: 16 }}>
              <div className="settings-card">
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  {lastScan && <span style={{ fontSize: 12, opacity: 0.5 }}>Letzter Scan: {new Date(lastScan).toLocaleTimeString()}</span>}
                  <button type="button" className="btn btn-primary btn-sm" onClick={runScan} disabled={scanning}>
                    {scanning ? "Scanne..." : "Jetzt scannen"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "permissions" && (
          <div className="settings-section">
            <div className="settings-section-header">
              <h3>Werkzeug-Berechtigungen</h3>
            </div>

            {permissions.length === 0 ? (
              <div className="settings-card" style={{ textAlign: "center", padding: 24 }}>
                <CheckCircle size={36} weight="thin" style={{ opacity: 0.3, marginBottom: 8 }} />
                <p style={{ margin: 0, opacity: 0.6 }}>Keine Berechtigungen gefunden.</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {permissions.map(p => (
                  <div key={p.name} className="settings-card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div>
                      <strong>{p.name}</strong>
                      <span style={{ fontSize: 11, opacity: 0.5, marginLeft: 8 }}>
                        (Standard: {p.default_permission})
                      </span>
                    </div>
                    <select
                      className="form-input"
                      style={{ width: "auto", fontSize: 12, padding: "2px 6px" }}
                      value={p.permission}
                      onChange={e => setToolPermission(p.name, e.target.value)}
                    >
                      <option value="allowe">Immer erlauben</option>
                      <option value="ask">Nachfragen</option>
                      <option value="deny">Verweigern</option>
                    </select>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {showCodeModal && (
        <div className="modal-overlay" onClick={cancelInstall} role="dialog" aria-modal="true" aria-label="Code-Vorschau">
          <div className="modal-content code-preview-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3><FileCode weight="regular" /> Code-Vorschau: {pendingInstallName}</h3>
              <button type="button" className="btn btn-ghost btn-icon" onClick={cancelInstall} aria-label="Schließen">
                <XCircle weight="regular" size={20} />
              </button>
            </div>
            <div className="modal-body">
              {previewLoading ? (
                <div className="loading-state" style={{ padding: 32, textAlign: "center" }}>
                  <span className="pulse" />
                  <span className="pulse" style={{ animationDelay: "0.2s" }} />
                  <span className="pulse" style={{ animationDelay: "0.4s" }} />
                  <p style={{ marginTop: 8, opacity: 0.6 }}>Generiere Code...</p>
                </div>
              ) : (
                <pre className="code-preview-pre"><code>{previewCode}</code></pre>
              )}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-primary btn-sm" onClick={confirmInstall} disabled={previewLoading}>
                <Plus weight="bold" size={16} /> Bestätigen & Installieren
              </button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={cancelInstall}>
                Ablehnen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


