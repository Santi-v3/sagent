import {
  CheckCircle,
  Cloud,
  FileCode,
  LockKey,
  ShieldCheck,
  Warning,
} from "@phosphor-icons/react";

import previewData from "@/data/cloud-approval-preview.json";

export function CloudApprovalPreview() {
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
        <strong>Cloud execution: {previewData.cloudExecution}</strong>
        <span>{previewData.previewType}</span>
        <code>{previewData.approvalStatus}</code>
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
            <code>{previewData.providerId}</code>
          </span>
        </div>
        <div>
          <ShieldCheck weight="regular" aria-hidden="true" />
          <span>
            <small>Purpose</small>
            <code>{previewData.purpose}</code>
          </span>
        </div>
        <div>
          <LockKey weight="regular" aria-hidden="true" />
          <span>
            <small>Scope</small>
            <code>{previewData.scope}</code>
          </span>
        </div>
        <div>
          <ShieldCheck weight="regular" aria-hidden="true" />
          <span>
            <small>Approval Status</small>
            <code>{previewData.approvalStatus}</code>
          </span>
        </div>
        <div>
          <CheckCircle weight="regular" aria-hidden="true" />
          <span>
            <small>explicit_confirmed</small>
            <code>{String(previewData.explicitConfirmed)}</code>
          </span>
        </div>
        <div>
          <CheckCircle weight="regular" aria-hidden="true" />
          <span>
            <small>secrets_excluded</small>
            <code>{String(previewData.secretsExcluded)}</code>
          </span>
        </div>
        <div>
          <LockKey weight="regular" aria-hidden="true" />
          <span>
            <small>full_repo_dump_blocked</small>
            <code>{String(previewData.fullRepoDumpBlocked)}</code>
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
            <code>{String(previewData.repoContextIncluded)}</code>
          </li>
          <li>
            <span>Diffs included</span>
            <code>{String(previewData.diffsIncluded)}</code>
          </li>
          <li>
            <span>Files included</span>
            <code>{String(previewData.filesIncluded)}</code>
          </li>
          <li>
            <span>Data was redacted</span>
            <code>{String(previewData.dataWasRedacted)}</code>
          </li>
          <li>
            <span>Bytes estimate</span>
            <code>{previewData.bytesEstimate}</code>
          </li>
        </ul>
      </div>

      <div className="cloud-preview-risk">
        <div className="cloud-preview-subheading">
          <Warning weight="regular" aria-hidden="true" />
          <h3>Risk Hints</h3>
        </div>
        <ul className="cloud-preview-risk-list">
          {previewData.riskHints.map((hint) => (
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
            Approval does not activate remote_http, does not read files, and does not transmit data.
          </p>
        </div>
      </div>

      <div className="cloud-preview-action-row">
        <span id="cloud-preview-disabled-reason">
          Keine Cloud-Ausführung: Die Approval-Preview ist eine read-only Vorschau ohne
          Runtime-Integration.
        </span>
      </div>
    </section>
  );
}
