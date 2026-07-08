"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowsClockwise, Brain, ChartBar, Cloud, XCircle } from "@phosphor-icons/react";

interface UsageStats {
  total_calls: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_duration_ms: number;
  total_estimated_cost: number;
  success_rate: number;
  recent_calls_24h: number;
  by_provider: Record<string, {calls: number; input_tokens: number; output_tokens: number; estimated_cost: number; errors: number}>;
  by_model: Record<string, {calls: number; input_tokens: number; output_tokens: number; estimated_cost: number; errors: number}>;
}

interface UsageEntry {
  id: string;
  timestamp: number;
  adapter_id: string;
  model: string;
  provider: string;
  transport: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  duration_ms: number;
  estimated_cost: number;
  success: boolean;
  error: string;
}

function fmt(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

function fmtDur(ms: number): string {
  if (ms >= 60_000) return (ms / 60_000).toFixed(1) + "min";
  if (ms >= 1_000) return (ms / 1_000).toFixed(1) + "s";
  return ms + "ms";
}

function fmtTime(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
}

export function UsageDashboard({ apiUrl }: { apiUrl: string }) {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [history, setHistory] = useState<UsageEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [sr, hr] = await Promise.all([
        fetch(`${apiUrl}/usage/stats`),
        fetch(`${apiUrl}/usage/history?limit=50`),
      ]);
      if (sr.ok) setStats(await sr.json());
      if (hr.ok) setHistory(await hr.json());
    } catch {} finally { setLoading(false); }
  }, [apiUrl]);

  useEffect(() => { void fetchData(); }, [fetchData]);

  if (loading && !stats) {
    return <div className="form-group"><p className="loading-text">Lade Verbrauchsdaten...</p></div>;
  }

  return (
    <div className="memory-panel">
      <div className="card-header">
        <h2>
          <ChartBar weight="regular" style={{ verticalAlign: "middle", marginRight: 6 }} />
          Usage Dashboard
        </h2>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => void fetchData()} disabled={loading}>
          <ArrowsClockwise weight={loading ? "bold" : "regular"} className={loading ? "spin" : ""} />
        </button>
      </div>

      {stats && (
        <>
          <div className="form-group" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            <div className="stat-card" style={{ textAlign: "center", padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
              <div style={{ fontSize: "1.5em", fontWeight: 700 }}>{fmt(stats.total_calls)}</div>
              <div className="text-muted" style={{ fontSize: "0.85em" }}>Total Calls</div>
            </div>
            <div className="stat-card" style={{ textAlign: "center", padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
              <div style={{ fontSize: "1.5em", fontWeight: 700 }}>{fmt(stats.total_input_tokens + stats.total_output_tokens)}</div>
              <div className="text-muted" style={{ fontSize: "0.85em" }}>Total Tokens</div>
            </div>
            <div className="stat-card" style={{ textAlign: "center", padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
              <div style={{ fontSize: "1.5em", fontWeight: 700 }}>{(stats.success_rate * 100).toFixed(0)}%</div>
              <div className="text-muted" style={{ fontSize: "0.85em" }}>Success Rate</div>
            </div>
            <div className="stat-card" style={{ textAlign: "center", padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
              <div style={{ fontSize: "1.5em", fontWeight: 700 }}>{fmtDur(stats.total_duration_ms)}</div>
              <div className="text-muted" style={{ fontSize: "0.85em" }}>Total Duration</div>
            </div>
            <div className="stat-card" style={{ textAlign: "center", padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
              <div style={{ fontSize: "1.5em", fontWeight: 700 }}>{stats.recent_calls_24h}</div>
              <div className="text-muted" style={{ fontSize: "0.85em" }}>Calls (24h)</div>
            </div>
            <div className="stat-card" style={{ textAlign: "center", padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
              <div style={{ fontSize: "1.5em", fontWeight: 700 }}>{Object.keys(stats.by_provider).length}</div>
              <div className="text-muted" style={{ fontSize: "0.85em" }}>Provider</div>
            </div>
            <div className="stat-card" style={{ textAlign: "center", padding: 12, background: "var(--surface2)", borderRadius: 8 }}>
              <div style={{ fontSize: "1.5em", fontWeight: 700 }}>${stats.total_estimated_cost.toFixed(4)}</div>
              <div className="text-muted" style={{ fontSize: "0.85em" }}>Geschätzte Kosten</div>
            </div>
          </div>

          {Object.keys(stats.by_provider).length > 0 && (
            <div className="form-group">
              <label className="form-label">
                <Cloud weight="regular" style={{ verticalAlign: "middle", marginRight: 4 }} />
                Nach Provider
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {Object.entries(stats.by_provider).sort((a, b) => b[1].calls - a[1].calls).map(([provider, data]) => (
                  <div key={provider} style={{ display: "flex", justifyContent: "space-between", padding: "6px 8px", background: "var(--surface2)", borderRadius: 6, fontSize: "0.9em" }}>
                    <span><strong>{provider}</strong> ({data.calls} calls)</span>
                    <span className="text-muted">{fmt(data.input_tokens)} in / {fmt(data.output_tokens)} out{data.errors > 0 ? ` / ${data.errors} errors` : ""}{data.estimated_cost > 0 ? ` / \$${data.estimated_cost.toFixed(4)}` : ""}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {Object.keys(stats.by_model).length > 0 && (
            <div className="form-group">
              <label className="form-label">
                <Brain weight="regular" style={{ verticalAlign: "middle", marginRight: 4 }} />
                Nach Modell
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                {Object.entries(stats.by_model).sort((a, b) => b[1].calls - a[1].calls).map(([model, data]) => (
                  <div key={model} style={{ display: "flex", justifyContent: "space-between", padding: "6px 8px", background: "var(--surface2)", borderRadius: 6, fontSize: "0.9em" }}>
                    <span><strong>{model}</strong> ({data.calls} calls)</span>
                    <span className="text-muted">{fmt(data.input_tokens)} in / {fmt(data.output_tokens)} out{data.errors > 0 ? ` / ${data.errors} errors` : ""}{data.estimated_cost > 0 ? ` / \$${data.estimated_cost.toFixed(4)}` : ""}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {history.length > 0 && (
        <div className="form-group">
          <label className="form-label">Letzte Aufrufe</label>
          <div style={{ maxHeight: 360, overflowY: "auto", display: "flex", flexDirection: "column", gap: 2 }}>
            {history.map(e => (
              <div key={e.id} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "4px 8px", background: "var(--surface2)", borderRadius: 4,
                fontSize: "0.85em", opacity: e.success ? 1 : 0.6,
              }}>
                <span style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
                  {e.success ? <span style={{ color: "var(--success)" }}>✓</span> : <XCircle weight="regular" color="var(--danger)" size={14} />}
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    <strong>{e.model.split(":")[0]}</strong>
                    <span className="text-muted" style={{ margin: "0 4px" }}>·</span>
                    <span className="text-muted">{e.provider}</span>
                  </span>
                </span>
                <span className="text-muted" style={{ whiteSpace: "nowrap", marginLeft: 8 }}>
                  {fmt(e.total_tokens)} tok · {fmtDur(e.duration_ms)}{e.estimated_cost > 0 ? ` · \$${e.estimated_cost.toFixed(6)}` : ""} · {fmtTime(e.timestamp)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
