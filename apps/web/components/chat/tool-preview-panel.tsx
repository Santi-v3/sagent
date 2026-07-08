"use client";

import { CheckCircle, Warning, XCircle } from "@phosphor-icons/react";

type ToolPreview = {
  name: string;
  preview: string;
  high_risk: boolean;
  iteration: number;
};

type Props = {
  previews: ToolPreview[];
  onApprove: (name: string) => void;
  onReject: (name: string) => void;
  watchfulMode: boolean;
};

export function ToolPreviewPanel({ previews, onApprove, onReject, watchfulMode }: Props) {
  if (previews.length === 0) return null;

  return (
    <div className="tool-preview-panel">
      <div className="tool-preview-header">
        <Warning weight="regular" />
        <span>Werkzeug-Vorschau</span>
      </div>
      <div className="tool-preview-list">
        {previews.map((tp, i) => (
          <div key={i} className={`tool-preview-item ${tp.high_risk ? "high-risk" : ""}`}>
            <div className="tool-preview-info">
              <span className="tool-preview-name">
                {tp.high_risk ? <Warning weight="regular" /> : <CheckCircle weight="regular" />}
                {tp.name}
              </span>
              <pre className="tool-preview-text">{tp.preview}</pre>
            </div>
            {watchfulMode && (
              <div className="tool-preview-actions">
                <button type="button" className="btn btn-sm btn-success" onClick={() => onApprove(tp.name)}>
                  <CheckCircle weight="regular" /> Ausführen
                </button>
                <button type="button" className="btn btn-sm btn-danger" onClick={() => onReject(tp.name)}>
                  <XCircle weight="regular" /> Ablehnen
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
