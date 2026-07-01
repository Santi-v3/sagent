"use client";

import {
  CheckCircle,
  Cloud,
  FileCode,
  LockKey,
  ShieldCheck,
  Warning,
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";

import previewData from "@/data/cloud-approval-preview.json";

type CloudApprovalPreviewResponse = {
  provider_id: string;
  purpose: string;
  scope: string;
  explicit_confirmed: boolean;
  is_approved: boolean;
  repo_context_included: boolean;
  diffs_included: boolean;
  files_included: boolean;
  data_was_redacted: boolean;
  secrets_excluded: boolean;
  full_repo_dump_blocked: boolean;
  bytes_estimate: number;
  approval_status: string;
  is_valid: boolean;
  risk_hints: string[];
};

type PreviewLoadState = "loading" | "local-api" | "offline-fallback";

const previewRequest = {
  provider_id: previewData.providerId,
  purpose: previewData.purpose,
  approved: false,
  explicit_confirmed: false,
  disclosure: {
    repo_context_included: false,
    diffs_included: false,
    files_included: false,
    data_was_redacted: false,
    bytes_estimate: 0,
  },
} as const;

function isSafeDeniedPreview(response: CloudApprovalPreviewResponse) {
  return (
    response.provider_id === previewData.providerId &&
    response.purpose === previewData.purpose &&
    response.scope === previewData.scope &&
    response.explicit_confirmed === false &&
    response.is_approved === false &&
    response.repo_context_included === false &&
    response.diffs_included === false &&
    response.files_included === false &&
    response.secrets_excluded === true &&
    response.full_repo_dump_blocked === true &&
    response.bytes_estimate === 0 &&
    response.approval_status === "no_decision" &&
    response.is_valid === false
  );
}

function toPreviewData(response: CloudApprovalPreviewResponse) {
  return {
    ...previewData,
    providerId: response.provider_id,
    purpose: response.purpose,
    scope: response.scope,
    explicitConfirmed: response.explicit_confirmed,
    isApproved: response.is_approved,
    repoContextIncluded: response.repo_context_included,
    diffsIncluded: response.diffs_included,
    filesIncluded: response.files_included,
    dataWasRedacted: response.data_was_redacted,
    secretsExcluded: response.secrets_excluded,
    fullRepoDumpBlocked: response.full_repo_dump_blocked,
    bytesEstimate: response.bytes_estimate,
    approvalStatus: response.approval_status,
    isValid: response.is_valid,
    riskHints: response.risk_hints,
  };
}

export function CloudApprovalPreview({ apiUrl }: { apiUrl: string }) {
  const [preview, setPreview] = useState(previewData);
  const [loadState, setLoadState] = useState<PreviewLoadState>("loading");

  useEffect(() => {
    const controller = new AbortController();

    fetch(`${apiUrl}/cloud/approval-preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(previewRequest),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Local preview request failed");
        const payload = (await response.json()) as CloudApprovalPreviewResponse;
        if (!isSafeDeniedPreview(payload)) {
          throw new Error("Local preview response violated the denied contract");
        }
        setPreview(toPreviewData(payload));
        setLoadState("local-api");
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") return;
        setPreview(previewData);
        setLoadState("offline-fallback");
      });

    return () => controller.abort();
  }, [apiUrl]);

  const sourceMessage = {
    loading: "Lokale Preview-Metadaten werden geprüft.",
    "local-api": "Read-only Metadaten aus der lokalen Agent-API.",
    "offline-fallback":
      "Lokale Agent-API nicht erreichbar. Statische Offline-Fallback-Vorschau aktiv.",
  }[loadState];

  return (
    <section className="cloud-preview-panel" aria-labelledby="cloud-preview-heading">
      <div className="cloud-preview-heading-row">
        <div>
          <p className="message-label">Cloud-Approval-Status</p>
          <h2 id="cloud-preview-heading">Cloud Approval Preview</h2>
        </div>
        <span className="cloud-preview-readonly-badge">
          <LockKey weight="regular" aria-hidden="true" />
          Preview only
        </span>
      </div>

      <div className="cloud-preview-state" role="status">
        <strong>Cloud execution: {preview.cloudExecution}</strong>
        <span>{preview.previewType}</span>
        <code>{preview.approvalStatus}</code>
      </div>

      <p className="cloud-preview-intro">
        Diese Vorschau zeigt die Offline-Cloud-Approval-Datenstruktur, die vor einer späten
        optionalen Cloud-Integration genutzt würde. Es findet kein Cloud-Aufruf, kein
        Netzwerkzugriff und keine Provideraktivierung statt.
      </p>

      <div className="cloud-preview-grid" aria-label="Provider und Status">
        <div>
          <Cloud weight="regular" aria-hidden="true" />
          <span>
            <small>Provider</small>
            <code>{preview.providerId}</code>
          </span>
        </div>
        <div>
          <ShieldCheck weight="regular" aria-hidden="true" />
          <span>
            <small>Purpose</small>
            <code>{preview.purpose}</code>
          </span>
        </div>
        <div>
          <LockKey weight="regular" aria-hidden="true" />
          <span>
            <small>Scope</small>
            <code>{preview.scope}</code>
          </span>
        </div>
        <div>
          <ShieldCheck weight="regular" aria-hidden="true" />
          <span>
            <small>Approval Status</small>
            <code>{preview.approvalStatus}</code>
          </span>
        </div>
        <div>
          <CheckCircle weight="regular" aria-hidden="true" />
          <span>
            <small>explicit_confirmed</small>
            <code>{String(preview.explicitConfirmed)}</code>
          </span>
        </div>
        <div>
          <CheckCircle weight="regular" aria-hidden="true" />
          <span>
            <small>secrets_excluded</small>
            <code>{String(preview.secretsExcluded)}</code>
          </span>
        </div>
        <div>
          <LockKey weight="regular" aria-hidden="true" />
          <span>
            <small>full_repo_dump_blocked</small>
            <code>{String(preview.fullRepoDumpBlocked)}</code>
          </span>
        </div>
      </div>

      <div className="cloud-preview-disclosure">
        <div className="cloud-preview-subheading">
          <FileCode weight="regular" aria-hidden="true" />
          <h3>Data Disclosure</h3>
        </div>
        <ul className="cloud-preview-disclosure-list">
          <li>
            <span>Repo context included</span>
            <code>{String(preview.repoContextIncluded)}</code>
          </li>
          <li>
            <span>Diffs included</span>
            <code>{String(preview.diffsIncluded)}</code>
          </li>
          <li>
            <span>Files included</span>
            <code>{String(preview.filesIncluded)}</code>
          </li>
          <li>
            <span>Data was redacted</span>
            <code>{String(preview.dataWasRedacted)}</code>
          </li>
          <li>
            <span>Bytes estimate</span>
            <code>{preview.bytesEstimate}</code>
          </li>
        </ul>
      </div>

      <div className="cloud-preview-risk">
        <div className="cloud-preview-subheading">
          <Warning weight="regular" aria-hidden="true" />
          <h3>Risk Hints</h3>
        </div>
        <ul className="cloud-preview-risk-list">
          {preview.riskHints.map((hint) => (
            <li key={hint}>
              <Warning weight="regular" aria-hidden="true" />
              <span>{hint}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="cloud-preview-privacy">
        <ShieldCheck weight="regular" aria-hidden="true" />
        <div>
          <p>Approval is a local contract only — no cloud call, no network, no provider build.</p>
          <p>
            Approval does not activate a remote transport, does not read files, and does not
            transmit data. Preview metadata has no tool authority.
          </p>
        </div>
      </div>

      <div className="cloud-preview-action-row">
        <span id="cloud-preview-disabled-reason" aria-live="polite">
          {sourceMessage} Keine Cloud-Ausführung: Die Approval-Preview ist read-only.
        </span>
      </div>
    </section>
  );
}
