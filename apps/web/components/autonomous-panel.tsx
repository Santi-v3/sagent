"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowsClockwise, Lightbulb, Play, Stop, X } from "@phosphor-icons/react";

interface Suggestion {
  id: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  command: string;
  created_at: number;
  dismissed: boolean;
}

const SEVERITY_COLORS: Record<string, string> = {
  info: "var(--accent)",
  warning: "var(--warning)",
  critical: "var(--danger)",
};

function fmtTime(ts: number): string {
  return new Date(ts * 1000).toLocaleString();
}

export function AutonomousModePanel({ apiUrl }: { apiUrl: string }) {
  const [enabled, setEnabled] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [status, setStatus] = useState<{
    last_scan: { timestamp: number | null; suggestions: number; duration_ms: number } | null;
    active_suggestions: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const [sr, sug] = await Promise.all([
        fetch(`${apiUrl}/autonomous/status`),
        fetch(`${apiUrl}/autonomous/suggestions`),
      ]);
      if (sr.ok) {
        const data = await sr.json();
        setEnabled(data.enabled);
        setStatus(data);
      }
      if (sug.ok) setSuggestions(await sug.json());
    } catch {} finally { setLoading(false); }
  }, [apiUrl]);

  useEffect(() => { void fetchStatus(); }, [fetchStatus]);

  async function toggle() {
    const newVal = !enabled;
    try {
      const r = await fetch(`${apiUrl}/autonomous/toggle?enabled=${newVal}`, { method: "POST" });
      if (r.ok) setEnabled(newVal);
    } catch {}
  }

  async function scanNow() {
    setScanning(true);
    try {
      await fetch(`${apiUrl}/autonomous/scan`, { method: "POST" });
      await fetchStatus();
    } catch {} finally { setScanning(false); }
  }

  async function dismiss(id: string) {
    try {
      await fetch(`${apiUrl}/autonomous/dismiss/${id}`, { method: "POST" });
      setSuggestions(prev => prev.filter(s => s.id !== id));
    } catch {}
  }

  async function dismissAll() {
    try {
      await fetch(`${apiUrl}/autonomous/dismiss-all`, { method: "POST" });
      setSuggestions([]);
    } catch {}
  }

  return (
    <>
      <div className="form-group">
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <label className="form-label" style={{ margin: 0 }}>Hintergrund-Scans</label>
          <button type="button"
            className={`btn btn-sm ${enabled ? "btn-primary" : "btn-ghost"}`}
            onClick={() => void toggle()}>
            {enabled ? <><Stop weight="regular" /> Aktiv</> : <><Play weight="regular" /> Inaktiv</>}
          </button>
        </div>
        <p className="text-muted" style={{ fontSize: "0.85em" }}>
          {enabled
            ? "Sagent scannt alle 5 Minuten dein Projekt auf Git-Änderungen, TODOs, Testergebnisse und veraltete Abhängigkeiten."
            : "Aktivieren für automatische Projekt-Scans und proaktive Vorschläge."}
        </p>
      </div>

      <div className="form-group">
        <div className="form-row">
          <button type="button" className="btn btn-sm" disabled={scanning}
            onClick={() => void scanNow()}>
            {scanning ? <ArrowsClockwise className="spin" weight="bold" /> : <ArrowsClockwise weight="regular" />}
            {scanning ? "Scanne..." : "Jetzt scannen"}
          </button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => void fetchStatus()}>
            <ArrowsClockwise weight="regular" />Aktualisieren
          </button>
        </div>
      </div>

      {status?.last_scan && (
        <div className="form-group" style={{ fontSize: "0.85em" }}>
          <span className="text-muted">
            Letzter Scan: {status.last_scan.timestamp ? fmtTime(status.last_scan.timestamp) : "nie"} · 
            {status.last_scan.suggestions} Vorschläge · {status.last_scan.duration_ms}ms
          </span>
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="form-group">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <label className="form-label" style={{ margin: 0 }}>
              <Lightbulb weight="regular" style={{ verticalAlign: "middle", marginRight: 4 }} />
              Aktive Vorschläge ({suggestions.length})
            </label>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => void dismissAll()}>
              <X weight="regular" />Alle verwerfen
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {suggestions.map(s => (
              <div key={s.id} style={{
                padding: "8px 10px", background: "var(--surface2)", borderRadius: 8,
                borderLeft: `3px solid ${SEVERITY_COLORS[s.severity] || "var(--accent)"}`,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <strong style={{ fontSize: "0.9em" }}>{s.title}</strong>
                    <span className={`badge badge-${s.severity === "critical" ? "danger" : s.severity === "warning" ? "warning" : "info"}`}
                      style={{ marginLeft: 6, fontSize: "0.75em" }}>
                      {s.type}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
                    {s.command && (
                      <span className="text-muted" style={{ fontSize: "0.8em", fontFamily: "monospace", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {s.command}
                      </span>
                    )}
                    <button type="button" className="btn btn-ghost btn-sm" style={{ padding: "0 4px", fontSize: "0.85em" }}
                      onClick={() => void dismiss(s.id)} title="Verwerfen">
                      <X weight="regular" size={14} />
                    </button>
                  </div>
                </div>
                {s.description && (
                  <div className="text-muted" style={{ fontSize: "0.85em", marginTop: 2 }}>{s.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && suggestions.length === 0 && (
        <div className="form-group">
          <p className="text-muted" style={{ textAlign: "center", padding: 20 }}>
            Keine Vorschläge. Führe einen Scan durch oder aktiviere den autonomen Modus.
          </p>
        </div>
      )}
    </>
  );
}
