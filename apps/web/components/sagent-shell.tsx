"use client";

import {
  ArrowUp,
  ArrowsClockwise,
  CheckCircle,
  CircleNotch,
  Circle,
  FileCode,
  HourglassMedium,
  Play,
  ShieldCheck,
  TerminalWindow,
  Warning,
  WarningCircle,
  XCircle,
} from "@phosphor-icons/react";
import { FormEvent, KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";

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

type TestProfile = {
  profile_id: string;
  command: string;
  timeout_seconds: number;
};

type TestResult = {
  result_id: string;
  profile_id: string;
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  passed: boolean;
  created_at: string;
  duration_ms: number;
  timed_out: boolean;
  output_truncated: boolean;
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
    message: "Der Plan ist freigegeben. Sichere, explizit ausgewählte Prüfungen sind jetzt möglich.",
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
  const [testProfiles, setTestProfiles] = useState<TestProfile[]>([]);
  const [selectedTestProfileId, setSelectedTestProfileId] = useState("");
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testProfileError, setTestProfileError] = useState("");
  const [isTestProfilesLoading, setIsTestProfilesLoading] = useState(false);
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [retryTest, setRetryTest] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetch(`${API_URL}/health`, { signal: controller.signal })
      .then((response) => setIsApiOnline(response.ok))
      .catch(() => setIsApiOnline(false));

    return () => controller.abort();
  }, []);

  const loadTestProfiles = useCallback(async () => {
    setIsTestProfilesLoading(true);
    setTestProfileError("");

    try {
      const response = await fetch(`${API_URL}/agent/test-profiles`);
      if (!response.ok) {
        throw new Error(`Profile request failed with status ${response.status}`);
      }
      const profiles = (await response.json()) as TestProfile[];
      setTestProfiles(profiles);
      setSelectedTestProfileId((current) => {
        if (profiles.some((profile) => profile.profile_id === current)) return current;
        return profiles.find((profile) => profile.profile_id === "project-tests")?.profile_id ??
          profiles[0]?.profile_id ??
          "";
      });
      setIsApiOnline(true);
    } catch {
      setTestProfileError("Die lokale Test-Allowlist konnte nicht geladen werden.");
      setIsApiOnline(false);
    } finally {
      setIsTestProfilesLoading(false);
    }
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
    setTestProfiles([]);
    setSelectedTestProfileId("");
    setTestResult(null);
    setTestProfileError("");
    setRetryTest(false);
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
    setRetryTest(false);

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
      if (data.task.approval_state === "approved") {
        void loadTestProfiles();
      }
    } catch {
      setError("Die Freigabeentscheidung konnte nicht gespeichert werden.");
      setIsApiOnline(false);
    } finally {
      setIsApprovalLoading(false);
    }
  }

  async function runTests() {
    const selectedProfile = testProfiles.find(
      (profile) => profile.profile_id === selectedTestProfileId,
    );
    if (
      !result ||
      result.approval_state !== "approved" ||
      !selectedProfile ||
      isTestLoading
    ) {
      return;
    }

    setIsTestLoading(true);
    setError("");
    setRetryDecision(null);
    setRetryTest(true);
    setTestResult(null);

    try {
      const response = await fetch(`${API_URL}/agent/run-tests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: result.task_id,
          profile_id: selectedProfile.profile_id,
          expected_command: selectedProfile.command,
          confirmed: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Test request failed with status ${response.status}`);
      }

      const data = (await response.json()) as TestResult;
      setTestResult(data);
      setRetryTest(false);
      setIsApiOnline(true);
    } catch {
      setError("Der lokale Testlauf konnte nicht gestartet werden.");
      setIsApiOnline(false);
    } finally {
      setIsTestLoading(false);
    }
  }

  function retryLastAction() {
    if (retryTest) {
      void runTests();
      return;
    }
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

                {result.approval_state === "approved" ? (
                  <section className="workflow-section test-section" aria-labelledby="tests-heading">
                    <div className="section-heading-row">
                      <h2 id="tests-heading">Tests</h2>
                      <span
                        className={`test-status ${
                          isTestLoading
                            ? "running"
                            : testResult?.passed
                              ? "passed"
                              : testResult
                                ? "failed"
                                : "ready"
                        }`}
                      >
                        {isTestLoading
                          ? "Läuft"
                          : testResult?.passed
                            ? "Bestanden"
                            : testResult
                              ? "Fehlgeschlagen"
                              : "Bereit"}
                      </span>
                    </div>
                    <p>
                      Nur der unten angezeigte Allowlist-Befehl wird lokal und ohne freie Shell
                      ausgeführt.
                    </p>

                    {testProfileError ? (
                      <div className="test-inline-error" role="alert">
                        <WarningCircle weight="regular" aria-hidden="true" />
                        <span>{testProfileError}</span>
                        <button type="button" onClick={() => void loadTestProfiles()}>
                          Erneut laden
                        </button>
                      </div>
                    ) : null}

                    {testProfiles.length ? (
                      <div className="test-controls">
                        <label htmlFor="test-profile">Testprofil</label>
                        <select
                          id="test-profile"
                          value={selectedTestProfileId}
                          disabled={isTestLoading}
                          onChange={(event) => {
                            setSelectedTestProfileId(event.target.value);
                            setTestResult(null);
                          }}
                        >
                          {testProfiles.map((profile) => (
                            <option key={profile.profile_id} value={profile.profile_id}>
                              {profile.profile_id}
                            </option>
                          ))}
                        </select>
                        <div className="test-command">
                          <TerminalWindow weight="regular" aria-hidden="true" />
                          <code>
                            {
                              testProfiles.find(
                                (profile) => profile.profile_id === selectedTestProfileId,
                              )?.command
                            }
                          </code>
                        </div>
                        <button
                          type="button"
                          className="test-run-button"
                          disabled={isTestLoading || !selectedTestProfileId}
                          onClick={() => void runTests()}
                        >
                          {isTestLoading ? (
                            <CircleNotch className="spin" weight="bold" aria-hidden="true" />
                          ) : (
                            <Play weight="fill" aria-hidden="true" />
                          )}
                          {isTestLoading ? "Tests laufen" : "Tests ausführen"}
                        </button>
                      </div>
                    ) : isTestProfilesLoading ? (
                      <div className="test-profile-loading" role="status">
                        Testprofile werden geladen …
                      </div>
                    ) : null}

                    {testResult ? (
                      <div className={`test-result ${testResult.passed ? "passed" : "failed"}`}>
                        <div className="test-result-summary">
                          {testResult.passed ? (
                            <CheckCircle weight="regular" aria-hidden="true" />
                          ) : (
                            <XCircle weight="regular" aria-hidden="true" />
                          )}
                          <div>
                            <strong>
                              {testResult.passed ? "Testlauf bestanden" : "Testlauf fehlgeschlagen"}
                            </strong>
                            <span>
                              Exit {testResult.exit_code} · {testResult.duration_ms} ms
                              {testResult.timed_out ? " · Zeitlimit erreicht" : ""}
                            </span>
                          </div>
                        </div>
                        <div className="test-logs">
                          <div className="test-logs-heading">
                            <span>Logs</span>
                            {testResult.output_truncated ? <span>gekürzt</span> : null}
                          </div>
                          {testResult.stdout ? (
                            <div>
                              <span className="test-log-label">stdout</span>
                              <pre tabIndex={0}>{testResult.stdout}</pre>
                            </div>
                          ) : null}
                          {testResult.stderr ? (
                            <div>
                              <span className="test-log-label">stderr</span>
                              <pre tabIndex={0}>{testResult.stderr}</pre>
                            </div>
                          ) : null}
                          {!testResult.stdout && !testResult.stderr ? (
                            <p>Der Testlauf hat keine Ausgabe erzeugt.</p>
                          ) : null}
                        </div>
                      </div>
                    ) : null}
                  </section>
                ) : null}
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
