"use client";

import { ShieldCheck } from "@phosphor-icons/react";
import { useEffect, useState } from "react";

const PERM_API = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8765";

type ToolInfo = { name: string; permission: string };

type Props = {
  overrides: Record<string, string>;
  onChange: (overrides: Record<string, string>) => void;
};

export function ConversationToolPerms({ overrides, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (open) loadTools(); }, [open]);

  async function loadTools() {
    setLoading(true);
    try {
      const r = await fetch(`${PERM_API}/tools/permissions`);
      if (r.ok) {
        const data = await r.json();
        setTools(data.tools.map((t: ToolInfo) => ({
          ...t,
          permission: overrides[t.name] || t.permission,
        })));
      }
    } catch { /* */ }
    finally { setLoading(false); }
  }

  function setPerm(name: string, perm: string) {
    setTools(prev => prev.map(t => t.name === name ? { ...t, permission: perm } : t));
    onChange({ ...overrides, [name]: perm });
  }

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        className="btn btn-ghost btn-sm btn-icon"
        onClick={() => setOpen(v => !v)}
        title="Tool-Berechtigungen für diesen Chat"
        aria-label="Tool-Berechtigungen"
      >
        <ShieldCheck weight="regular" aria-hidden="true" />
      </button>

      {open && (
        <>
          <div className="sidebar-backdrop" style={{ position: "fixed", inset: 0, zIndex: 99 }} onClick={() => setOpen(false)} />
          <div style={{
            position: "absolute", top: "100%", right: 0, zIndex: 100,
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 8, padding: 12, minWidth: 260, boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
              Tool-Berechtigungen (dieser Chat)
            </div>
            {loading ? (
              <div style={{ fontSize: 12, opacity: 0.5 }}>Lade…</div>
            ) : tools.length === 0 ? (
              <div style={{ fontSize: 12, opacity: 0.5 }}>Keine Tools verfügbar.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 300, overflowY: "auto" }}>
                {tools.map(t => (
                  <div key={t.name} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
                    <span style={{ flex: 1, whiteSpace: "nowrap" }}>{t.name}</span>
                    <select
                      value={t.permission}
                      onChange={e => setPerm(t.name, e.target.value)}
                      style={{ fontSize: 11, padding: "2px 4px", width: 90 }}
                    >
                      <option value="allow">Erlauben</option>
                      <option value="ask">Nachfragen</option>
                      <option value="deny">Sperren</option>
                    </select>
                  </div>
                ))}
              </div>
            )}
            <div style={{ fontSize: 11, opacity: 0.4, marginTop: 8 }}>
              Überschreibt die globalen Einstellungen für diesen Chat.
            </div>
          </div>
        </>
      )}
    </div>
  );
}
