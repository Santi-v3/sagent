"use client";

import {
  ArrowUp,
  CheckCircle,
  Circle,
  WarningCircle,
} from "@phosphor-icons/react";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

type TaskResponse = {
  status: "accepted";
  message: string;
  next_steps: string[];
};

const API_URL = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8765";

const sampleTasks = [
  "API-Verbindung prüfen",
  "Agent-Datenmodell planen",
  "UI-Komponente beschreiben",
  "Test-Setup vorbereiten",
];

export function SagentShell() {
  const [task, setTask] = useState("");
  const [submittedTask, setSubmittedTask] = useState("");
  const [result, setResult] = useState<TaskResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
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
    setResult(null);
    setSubmittedTask(normalizedTask);

    try {
      const response = await fetch(`${API_URL}/agent/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: normalizedTask }),
      });

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = (await response.json()) as TaskResponse;
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
                <h1>Was soll Sagent bauen?</h1>
                <p>
                  Aufgaben werden in dieser Minimalversion nur lokal angenommen und noch
                  nicht ausgeführt.
                </p>
              </div>
            )}

            {isLoading ? (
              <div className="loading-state" role="status">
                Aufgabe wird lokal verarbeitet …
              </div>
            ) : null}

            {result ? (
              <article className="message agent-message">
                <p className="message-label">Sagent</p>
                <div className="result-status">
                  <CheckCircle weight="regular" aria-hidden="true" />
                  <span>Angenommen</span>
                </div>
                <p>{result.message}</p>
                <h2>Nächste Schritte</h2>
                <ol>
                  {result.next_steps.map((step) => (
                    <li key={step}>{step}</li>
                  ))}
                </ol>
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
                  <span>{isLoading ? "Wird gesendet" : "Senden"}</span>
                  <ArrowUp weight="bold" aria-hidden="true" />
                </button>
              </div>
            </form>

            {error ? (
              <div className="error-banner" role="alert">
                <WarningCircle weight="regular" aria-hidden="true" />
                <span>{error}</span>
                <button type="button" onClick={() => void submitTask()}>
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
