"use client";

import {
  ArrowsClockwise,
  CheckCircle,
  CircleNotch,
  FileCode,
  LockKey,
  ShieldCheck,
  Warning,
  WarningCircle,
  XCircle,
} from "@phosphor-icons/react";
import { useCallback, useState } from "react";

type CodeEditStatus = "pending" | "approved" | "applied" | "stale";

type PreviewData = {
  change_set_id: string;
  proposal_hash: string;
  status: CodeEditStatus;
  diff: string;
  approval_required: true;
  shell_executed: false;
  git_executed: false;
  network_used: false;
  model_authority: false;
};

type ApplyData = {
  change_set_id: string;
  proposal_hash: string;
  status: CodeEditStatus;
  shell_executed: false;
  git_executed: false;
  network_used: false;
  model_authority: false;
};

type PanelStep = "idle" | "previewing" | "previewed" | "approving" | "approved" | "applying" | "applied" | "error";

type Props = {
  apiUrl: string;
};

export function CodeEditPreviewPanel({ apiUrl }: Props) {
  const [path, setPath] = useState("");
  const [content, setContent] = useState("");
  const [description, setDescription] = useState("");
  const [step, setStep] = useState<PanelStep>("idle");
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [applyResult, setApplyResult] = useState<ApplyData | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [previewedPath, setPreviewedPath] = useState("");
  const [previewedContent, setPreviewedContent] = useState("");

  const reset = useCallback(() => {
    setStep("idle");
    setPreview(null);
    setApplyResult(null);
    setError("");
    setIsLoading(false);
    setPreviewedPath("");
    setPreviewedContent("");
  }, []);

  const isStale = preview != null && (
    path.trim() !== previewedPath || content !== previewedContent
  );

  const canPreview = path.trim().length > 0 && description.trim().length > 0 && step === "idle";

  const canApprove = step === "previewed" && preview?.status === "pending" && !isStale;
  const canApply = step === "approved" && preview?.status === "approved" && !isStale;

  async function handlePreview() {
    if (!canPreview) return;
    setIsLoading(true);
    setError("");
    setPreview(null);
    setApplyResult(null);

    try {
      const response = await fetch(`${apiUrl}/agent/code-edits/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: path.trim(),
          content,
          change_description: description.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Preview request failed with status ${response.status}`);
      }

      setPreviewedPath(path.trim());
      setPreviewedContent(content);
      const data = (await response.json()) as PreviewData;
      setPreview(data);
      setStep("previewed");
    } catch {
      setError("Code-Edit-Vorschau konnte nicht geladen werden.");
      setStep("error");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleApprove() {
    if (!preview || preview.status !== "pending") return;
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(`${apiUrl}/agent/code-edits/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          change_set_id: preview.change_set_id,
          proposal_hash: preview.proposal_hash,
          approved: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Approval request failed with status ${response.status}`);
      }

      const data = (await response.json()) as PreviewData;
      setPreview(data);
      setStep("approved");
    } catch {
      setError("Die Freigabe konnte nicht gespeichert werden.");
      setStep("error");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleApply() {
    if (!preview || preview.status !== "approved") return;
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(`${apiUrl}/agent/code-edits/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          change_set_id: preview.change_set_id,
          proposal_hash: preview.proposal_hash,
          confirmed: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Apply request failed with status ${response.status}`);
      }

      const data = (await response.json()) as ApplyData;
      setApplyResult(data);
      setStep("applied");
    } catch {
      setError("Die Änderung konnte nicht angewendet werden.");
      setStep("error");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="code-edit-panel" aria-labelledby="code-edit-heading">
      <div className="code-edit-heading-row">
        <div>
          <p className="message-label">Lokale Code-Änderung</p>
          <h2 id="code-edit-heading">Code Edit</h2>
        </div>
        <span className="code-edit-readonly-badge">
          <LockKey weight="regular" aria-hidden="true" />
          Read-only
        </span>
      </div>

      <p className="code-edit-intro">
        Datei-Pfad und Inhalt angeben, um einen sicheren, nicht-ausführenden
        Vorschlag zu erstellen.
      </p>

      <div className="code-edit-form">
        <label htmlFor="code-edit-path">Dateipfad</label>
        <input
          id="code-edit-path"
          type="text"
          value={path}
          onChange={(e) => { setPath(e.target.value); if (step !== "idle") reset(); }}
          placeholder="src/example.ts"
          disabled={isLoading}
          autoComplete="off"
          spellCheck={false}
        />

        <label htmlFor="code-edit-content">Neuer Inhalt</label>
        <textarea
          id="code-edit-content"
          value={content}
          onChange={(e) => { setContent(e.target.value); if (step !== "idle") reset(); }}
          placeholder="// Neuer Dateiinhalt …"
          rows={6}
          disabled={isLoading}
          spellCheck={false}
        />

        <label htmlFor="code-edit-description">Änderungsbeschreibung</label>
        <input
          id="code-edit-description"
          type="text"
          value={description}
          onChange={(e) => { setDescription(e.target.value); if (step !== "idle") reset(); }}
          placeholder="z. B. Funktion hinzufügen"
          disabled={isLoading}
          autoComplete="off"
        />
      </div>

      <div className="code-edit-actions">
        {step === "idle" || step === "error" ? (
          <button
            type="button"
            className="code-edit-button preview"
            disabled={!canPreview || isLoading}
            onClick={() => void handlePreview()}
          >
            {isLoading ? (
              <CircleNotch className="spin" weight="bold" aria-hidden="true" />
            ) : (
              <FileCode weight="regular" aria-hidden="true" />
            )}
            {isLoading ? "Vorschau wird erstellt" : "Vorschau anzeigen"}
          </button>
        ) : null}

        {canApprove && !isStale ? (
          <div className="code-edit-approval-row">
            <button
              type="button"
              className="code-edit-button approve"
              disabled={isLoading}
              onClick={() => void handleApprove()}
            >
              {isLoading ? (
                <CircleNotch className="spin" weight="bold" aria-hidden="true" />
              ) : (
                <CheckCircle weight="regular" aria-hidden="true" />
              )}
              {isLoading ? "Freigabe läuft" : "Freigeben"}
            </button>
            <button
              type="button"
              className="code-edit-button cancel"
              disabled={isLoading}
              onClick={reset}
            >
              <XCircle weight="regular" aria-hidden="true" />
              Verwerfen
            </button>
          </div>
        ) : null}

        {step === "approved" && canApply && !isStale ? (
          <div className="code-edit-approval-row">
            <button
              type="button"
              className="code-edit-button apply"
              disabled={isLoading}
              onClick={() => void handleApply()}
            >
              {isLoading ? (
                <CircleNotch className="spin" weight="bold" aria-hidden="true" />
              ) : (
                <ArrowsClockwise weight="regular" aria-hidden="true" />
              )}
              {isLoading ? "Wird angewendet" : "Änderung anwenden"}
            </button>
            <button
              type="button"
              className="code-edit-button cancel"
              disabled={isLoading}
              onClick={reset}
            >
              <XCircle weight="regular" aria-hidden="true" />
              Zurücksetzen
            </button>
          </div>
        ) : null}

        {isStale ? (
          <div className="code-edit-stale-banner" role="status">
            <Warning weight="regular" aria-hidden="true" />
            <span>Vorschlag ist veraltet – Pfad oder Inhalt wurde geändert.</span>
            <button type="button" className="code-edit-button cancel" onClick={reset}>
              Zurücksetzen
            </button>
          </div>
        ) : null}
      </div>

      {error ? (
        <div className="code-edit-error" role="alert">
          <WarningCircle weight="regular" aria-hidden="true" />
          <span>{error}</span>
          <button type="button" onClick={reset}>
            Zurücksetzen
          </button>
        </div>
      ) : null}

      {preview ? (
        <div className="code-edit-result">
          <div className="code-edit-result-header">
            <span className="code-edit-status-badge" data-status={preview.status}>
              {preview.status === "pending"
                ? "Ausstehend"
                : preview.status === "approved"
                  ? "Freigegeben"
                  : preview.status === "applied"
                    ? "Angewendet"
                    : "Veraltet"}
            </span>
            <code className="code-edit-hash">{preview.proposal_hash.slice(0, 12)}</code>
          </div>

          <div className="code-edit-security-row">
            <ShieldCheck weight="regular" aria-hidden="true" />
            <span>Keine Shell · Kein Git · Kein Netzwerk · Kein Modell</span>
          </div>

          <div className="code-edit-diff-block">
            <span>Diff</span>
            <pre tabIndex={0}>{preview.diff}</pre>
          </div>
        </div>
      ) : null}

      {applyResult ? (
        <div className="code-edit-apply-result">
          <CheckCircle weight="regular" aria-hidden="true" />
          <div>
            <strong>Angewendet</strong>
            <span>
              Status: {applyResult.status} · Keine Shell · Kein Git · Kein Netzwerk
            </span>
          </div>
        </div>
      ) : null}
    </section>
  );
}
