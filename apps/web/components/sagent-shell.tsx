"use client";

import {
  ArrowUp,
  ArrowsClockwise,
  CheckCircle,
  Circle,
  FileCode,
  HourglassMedium,
  ShieldCheck,
  Warning,
  WarningCircle,
  XCircle,
} from "@phosphor-icons/react";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

type ApprovalState = "pending" | "approved" | "rejected" | "needs_changes";
type ApprovalDecision = Exclude<ApprovalState, "pending">;

type PlanStep = {
  position: number;
  title: string;
  description: string;
};

type ChangeProposal = {
  summary: string;
  risk_level: "low" | "medium" | "high";
  affected_files: string[];
  required_approvals: string[];
};

type PlannedTask = {
  task_id: string;
  task: string;
  goal: string;
  steps: PlanStep[];
  risks: string[];
  next_actions: string[];
  proposal: ChangeProposal;
  approval_state: ApprovalState;
  created_at: string;
  updated_at: string;
};

type ApprovalResponse = {
  message: string;
  task: PlannedTask;
};

const API_URL = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8765";

const sampleTasks = [
  "Approval-Flow simulieren",
  "Agent-Datenmodell planen",
  "WorkspaceGuard vorbereiten",
  "Test-Setup erweitern",
];

const approvalCopy: Record<ApprovalState, { label: string; message: string }> = {
  pending: {
    label: "Freigabe ausstehend",
    message: "Prüfe Plan, Risiken und Änderungsvorschlag, bevor du entscheidest.",
  },
  approved: {
    label: "Freigegeben",
    message: "Der Vorschlag ist freigegeben. Diese Simulation führt trotzdem nichts aus.",
  },
  rejected: {
    label: "Abgelehnt",
    message: "Der Vorschlag wurde verworfen und wird nicht ausgeführt.",
  },
  needs_changes: {
    label: "Überarbeitung nötig",
    message: "Der Vorschlag benötigt Änderungen, bevor eine neue Freigabe möglich ist.",
  },
};

const riskCopy: Record<ChangeProposal["risk_level"], string> = {
  low: "niedrig",
  medium: "mittel",
  high: "hoch",
};

function ApprovalIcon({ state }: { state: ApprovalState }) {
  if (state === "approved") return <CheckCircle weight="regular" aria-hidden="true" />;
  if (state === "rejected") return <XCircle weight="regular" aria-hidden="true" />;
  if (state === "needs_changes") {
    return <ArrowsClockwise weight="regular" aria-hidden="true" />;
  }
  return <HourglassMedium weight="regular" aria-hidden="true" />;
}

export function SagentShell() {
  const [task, setTask] = useState("");
  const [submittedTask, setSubmittedTask] = useState("");
  const [result, setResult] = useState<PlannedTask | null>(null);
  const [approvalMessage, setApprovalMessage] = useState("");
  const [error, setError] = useState("");
  const [retryDecision, setRetryDecision] = useState<ApprovalDecision | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isApprovalLoading, setIsApprovalLoading] = useState(false);
  const [isApiOnline, setIsApiOnline] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetch(`${API_URL}/health`, { signal: controller.signal })
      .then((response) => setIsApiOnline(response.ok))
      .catch(() => setIsApiOnline(false));

    return () => controller.abort();
  }, []);

  async function submitTask(event?: FormEvent) {
    event?.preventDefault();
    const normalizedTask = task.trim();
    if (!normalizedTask || isLoading) return;

    setIsLoading(true);
    setError("");
    setRetryDecision(null);
    setResult(null);
    setApprovalMessage("");
    setSubmittedTask(normalizedTask);

    try {
      const response = await fetch(`${API_URL}/agent/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: normalizedTask }),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = (await response.json()) as PlannedTask;
      setResult(data);
      setTask("");
      setIsApiOnline(true);
    } catch {
      setError("Verbindung zur lokalen API fehlgeschlagen.");
      setIsApiOnline(false);
    } finally {
      setIsLoading(false);
    }
  }

  async function decide(decision: ApprovalDecision) {
    if (!result || result.approval_state !== "pending" || isApprovalLoading) return;

    setIsApprovalLoading(true);
    setError("");
    setRetryDecision(decision);

    try {
      const response = await fetch(`${API_URL}/agent/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: result.task_id, decision }),
      });

      if (!response.ok) {
        throw new Error(`Approval request failed with status ${response.status}`);
      }

      const data = (await response.json()) as ApprovalResponse;
      setResult(data.task);
      setApprovalMessage(data.message);
      setRetryDecision(null);
      setIsApiOnline(true);
    } catch {
      setError("Die Freigabeentscheidung konnte nicht gespeichert werden.");
      setIsApiOnline(false);
    } finally {
      setIsApprovalLoading(false);
    }
  }

  function retryLastAction() {
    if (retryDecision) {
      void decide(retryDecision);
      return;
    }
    void submitTask();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitTask();
    }
  }

  function selectSampleTask(sample: string) {
    setTask(sample);
    textareaRef.current?.focus();
  }

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Projekt-Navigation">
        <div className="brand">Sagent</div>

        <section className="sidebar-section">
          <h2>Projekte</h2>
          <div className="project-item" aria-current="page">
            <span>sagent</span>
          </div>
        </section>

        <section className="sidebar-section history">
          <h2>Verlauf</h2>
          <div className="history-list">
            {sampleTasks.map((sample) => (
              <button key={sample} type="button" onClick={() => selectSampleTask(sample)}>
                {sample}
              </button>
            ))}
          </div>
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <strong>sagent</strong>
          <div className={isApiOnline ? "api-state online" : "api-state"}>
            <Circle weight="fill" aria-hidden="true" />
            <span>{isApiOnline ? "Lokal" : "Offline"}</span>
          </div>
        </header>

        <div className="thread" aria-live="polite">
          <div className="thread-content">
            {submittedTask ? (
              <article className="message user-message">
                <p className="message-label">Du</p>
                <p>{submittedTask}</p>
              </article>
            ) : (
              <div className="empty-state">
                <p className="message-label">Lokaler Developer-Agent</p>
                <h1>Was soll Sagent planen?</h1>
                <p>
                  Sagent simuliert einen sicheren Plan und wartet vor jeder möglichen
                  Änderung auf deine Entscheidung.
                </p>
              </div>
            )}

            {isLoading ? (
              <div className="loading-state" role="status">
                Sicherer Plan wird lokal erstellt …
              </div>
            ) : null}

            {result ? (
              <article className="message agent-message">
                <p className="message-label">Sagent</p>
                <div className={`approval-status status-${result.approval_state}`}>
                  <ApprovalIcon state={result.approval_state} />
                  <span>{approvalCopy[result.approval_state].label}</span>
                </div>
                <p>{result.goal}</p>

                <section className="workflow-section" aria-labelledby="plan-heading">
                  <h2 id="plan-heading">Plan</h2>
                  <ol className="plan-steps">
                    {result.steps.map((step) => (
                      <li key={step.position}>
                        <div>
                          <strong>{step.title}</strong>
                          <p>{step.description}</p>
                        </div>
                      </li>
                    ))}
                  </ol>
                </section>

                <section className="workflow-section" aria-labelledby="risks-heading">
                  <h2 id="risks-heading">Risiken</h2>
                  <ul className="risk-list">
                    {result.risks.map((risk) => (
                      <li key={risk}>
                        <Warning weight="regular" aria-hidden="true" />
                        <span>{risk}</span>
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="workflow-section" aria-labelledby="proposal-heading">
                  <div className="section-heading-row">
                    <h2 id="proposal-heading">Änderungsvorschlag</h2>
                    <span className={`risk-badge risk-${result.proposal.risk_level}`}>
                      Risiko: {riskCopy[result.proposal.risk_level]}
                    </span>
                  </div>
                  <p>{result.proposal.summary}</p>
                  <dl className="proposal-details">
                    <div>
                      <dt>
                        <FileCode weight="regular" aria-hidden="true" />
                        Betroffene Bereiche
                      </dt>
                      <dd>
                        {result.proposal.affected_files.length
                          ? result.proposal.affected_files.join(", ")
                          : "Nach sicherer Projektanalyse festzulegen"}
                      </dd>
                    </div>
                    <div>
                      <dt>
                        <ShieldCheck weight="regular" aria-hidden="true" />
                        Benötigte Freigabe
                      </dt>
                      <dd>Menschliche Prüfung</dd>
                    </div>
                  </dl>
                </section>

                <section className="workflow-section approval-section" aria-labelledby="approval-heading">
                  <h2 id="approval-heading">Entscheidung</h2>
                  <p>{approvalMessage || approvalCopy[result.approval_state].message}</p>
                  {result.approval_state === "pending" ? (
                    <div className="approval-actions">
                      <button
                        type="button"
                        className="approval-button approve"
                        disabled={isApprovalLoading}
                        onClick={() => void decide("approved")}
                      >
                        <CheckCircle weight="regular" aria-hidden="true" />
                        Freigeben
                      </button>
                      <button
                        type="button"
                        className="approval-button revise"
                        disabled={isApprovalLoading}
                        onClick={() => void decide("needs_changes")}
                      >
                        <ArrowsClockwise weight="regular" aria-hidden="true" />
                        Überarbeiten
                      </button>
                      <button
                        type="button"
                        className="approval-button reject"
                        disabled={isApprovalLoading}
                        onClick={() => void decide("rejected")}
                      >
                        <XCircle weight="regular" aria-hidden="true" />
                        Ablehnen
                      </button>
                    </div>
                  ) : null}
                </section>
              </article>
            ) : null}
          </div>

          <div className="composer-wrap">
            <form className="composer" onSubmit={submitTask}>
              <label htmlFor="task-input" className="sr-only">
                Aufgabe für Sagent
              </label>
              <textarea
                ref={textareaRef}
                id="task-input"
                value={task}
                onChange={(event) => setTask(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Aufgabe an Sagent senden"
                rows={3}
                maxLength={4000}
              />
              <div className="composer-footer">
                <span>Shift + Enter für neue Zeile</span>
                <button type="submit" disabled={!task.trim() || isLoading}>
                  <span>{isLoading ? "Plant" : "Plan erstellen"}</span>
                  <ArrowUp weight="bold" aria-hidden="true" />
                </button>
              </div>
            </form>

            {error ? (
              <div className="error-banner" role="alert">
                <WarningCircle weight="regular" aria-hidden="true" />
                <span>{error}</span>
                <button type="button" onClick={retryLastAction}>
                  Erneut versuchen
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}
