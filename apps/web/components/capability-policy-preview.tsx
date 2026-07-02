"use client";

import {
  CheckCircle,
  LockKey,
  ShieldCheck,
  Warning,
  XCircle,
} from "@phosphor-icons/react";
import { useEffect, useState } from "react";

import fallbackData from "@/data/capability-policy-preview.json";

type CapabilityEntry = {
  name: string;
  mode: string;
  decision_for_execution: string;
  requires_approval: boolean;
  preview_only: boolean;
  disabled: boolean;
};

type CapabilityPreviewResponse = {
  policy_version: "1.0.0";
  capabilities: CapabilityEntry[];
  shell_executed: false;
  git_executed: false;
  network_used: false;
  cloud_used: false;
  model_called: false;
  runtime_activated: false;
};

type EntryDisplay = {
  name: string;
  mode: string;
  decision: string;
  requiresApproval: boolean;
  previewOnly: boolean;
  disabled: boolean;
};

type PreviewLoadState = "loading" | "local-api" | "offline-fallback";

function toEntryDisplay(
  entry: CapabilityEntry,
): EntryDisplay {
  return {
    name: entry.name,
    mode: entry.mode,
    decision: entry.decision_for_execution,
    requiresApproval: entry.requires_approval,
    previewOnly: entry.preview_only,
    disabled: entry.disabled,
  };
}

const fallbackEntries: EntryDisplay[] = fallbackData.capabilities.map(
  (e) =>
    ({
      name: e.name,
      mode: e.mode,
      decision: e.decisionForExecution,
      requiresApproval: e.requiresApproval,
      previewOnly: e.previewOnly,
      disabled: e.disabled,
    }) as EntryDisplay,
);

function isSafeResponse(
  response: unknown,
): response is { capabilities: CapabilityEntry[] } {
  if (typeof response !== "object" || response === null) return false;
  const data = response as Record<string, unknown>;
  if (!Array.isArray(data.capabilities)) return false;
  return true;
}

const decisionLabel: Record<string, { label: string; color: string }> = {
  allowed: { label: "Allowed", color: "var(--success)" },
  needs_approval: { label: "Needs Approval", color: "var(--warning)" },
  preview_only: { label: "Preview Only", color: "var(--info)" },
  denied: { label: "Denied", color: "var(--danger)" },
};

function DecisionIcon({ decision }: { decision: string }) {
  if (decision === "allowed") {
    return <CheckCircle weight="regular" aria-hidden="true" />;
  }
  if (decision === "needs_approval") {
    return <Warning weight="regular" aria-hidden="true" />;
  }
  if (decision === "preview_only") {
    return <LockKey weight="regular" aria-hidden="true" />;
  }
  return <XCircle weight="regular" aria-hidden="true" />;
}

export function CapabilityPolicyPreview({
  apiUrl,
}: {
  apiUrl: string;
}) {
  const [entries, setEntries] = useState<EntryDisplay[]>(fallbackEntries);
  const [loadState, setLoadState] = useState<PreviewLoadState>("loading");

  useEffect(() => {
    const controller = new AbortController();

    fetch(`${apiUrl}/capabilities/preview`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Capability preview request failed");
        const payload =
          (await response.json()) as CapabilityPreviewResponse;
        if (!isSafeResponse(payload)) {
          throw new Error("Response violated the safe metadata contract");
        }
        setEntries(payload.capabilities.map(toEntryDisplay));
        setLoadState("local-api");
      })
      .catch((requestError: unknown) => {
        if (
          requestError instanceof DOMException &&
          requestError.name === "AbortError"
        )
          return;
        setEntries(fallbackEntries);
        setLoadState("offline-fallback");
      });

    return () => controller.abort();
  }, [apiUrl]);

  const sourceMessage = {
    loading: "Lokale Capability-Policy-Metadaten werden geladen.",
    "local-api": "Read-only Metadaten aus der lokalen Agent-API.",
    "offline-fallback":
      "Lokale Agent-API nicht erreichbar. Statische Offline-Fallback-Vorschau aktiv.",
  }[loadState];

  return (
    <section
      className="capability-policy-preview"
      aria-labelledby="capability-policy-heading"
    >
      <div className="capability-policy-heading-row">
        <div>
          <p className="message-label">Capability Policy Preview</p>
          <h2 id="capability-policy-heading">Capability Policy</h2>
        </div>
        <span className="capability-policy-readonly-badge">
          <LockKey weight="regular" aria-hidden="true" />
          Read-only preview
        </span>
      </div>

      <div className="capability-policy-intro">
        <ShieldCheck weight="regular" aria-hidden="true" />
        <span>
          No runtime actions are enabled here. This is a read-only preview of
          the capability policy — no shell, git, network, cloud, or model
          action is executed.
        </span>
      </div>

      <div className="capability-policy-table">
        <div className="capability-policy-table-head">
          <span>Capability</span>
          <span>Mode</span>
          <span>Decision</span>
        </div>
        {entries.map((entry) => (
          <div
            key={entry.name}
            className={`capability-policy-row ${entry.disabled ? "disabled" : ""}`}
          >
            <span className="capability-name">
              <code>{entry.name}</code>
            </span>
            <span className="capability-mode">
              <code>{entry.mode}</code>
            </span>
            <span
              className="capability-decision"
              style={{ color: decisionLabel[entry.decision]?.color }}
            >
              <DecisionIcon decision={entry.decision} />
              <span>{decisionLabel[entry.decision]?.label ?? entry.decision}</span>
            </span>
          </div>
        ))}
      </div>

      <div className="capability-policy-safety">
        <ShieldCheck weight="regular" aria-hidden="true" />
        <div>
          <p>
            Safety flags: Shell=No, Git=No, Network=No, Cloud=No, Model=No,
            Runtime=No.
          </p>
          <p>No runtime actions are activated by this preview.</p>
        </div>
      </div>

      <div className="capability-policy-action-row">
        <span aria-live="polite">
          {sourceMessage}
        </span>
      </div>
    </section>
  );
}
