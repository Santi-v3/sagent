import {
  CheckCircle,
  Cpu,
  Flask,
  LockKey,
  Play,
  ShieldCheck,
  TerminalWindow,
} from "@phosphor-icons/react";

import benchmarkStatus from "@/data/benchmark-status.json";

export function BenchmarkStatus() {
  return (
    <section className="benchmark-panel" aria-labelledby="benchmark-heading">
      <div className="benchmark-heading-row">
        <div>
          <p className="message-label">Lokale Modell-Evaluation</p>
          <h2 id="benchmark-heading">Benchmark-Status</h2>
        </div>
        <span className="benchmark-readonly-badge">
          <LockKey weight="regular" aria-hidden="true" />
          Nur Information
        </span>
      </div>

      <div className="benchmark-state" role="status">
        <CheckCircle weight="regular" aria-hidden="true" />
        <div>
          <strong>{benchmarkStatus.status}</strong>
          <span>{benchmarkStatus.liveRunStatus}</span>
        </div>
        <code>{benchmarkStatus.confirmationState}</code>
      </div>

      <p className="benchmark-intro">
        Echte Läufe sind ausschließlich lokal, nach ausdrücklicher Bestätigung und mit der
        bestehenden IPv4-Loopback-Konfiguration möglich. Für diese Sektion wird beim Laden
        nichts geprüft oder ausgeführt.
      </p>

      <div className="benchmark-provider-grid" aria-label="Erlaubte lokale Provider">
        {benchmarkStatus.providers.map((provider) => (
          <div key={provider.name}>
            <Cpu weight="regular" aria-hidden="true" />
            <span>
              <small>{provider.name}</small>
              <code>{provider.endpoint}</code>
            </span>
          </div>
        ))}
      </div>

      <div className="benchmark-task-block">
        <div className="benchmark-subheading">
          <Flask weight="regular" aria-hidden="true" />
          <h3>Synthetische Aufgaben</h3>
        </div>
        <ol className="benchmark-task-list">
          {benchmarkStatus.tasks.map((task, index) => (
            <li key={task.taskId}>
              <span>{index + 1}</span>
              <div>
                <strong>{task.title}</strong>
                <p>{task.description}</p>
                <code>{task.taskId}</code>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div className="benchmark-command">
        <div>
          <TerminalWindow weight="regular" aria-hidden="true" />
          <span>Sicherer Standardaufruf</span>
        </div>
        <pre tabIndex={0}>{benchmarkStatus.safeCommand}</pre>
        <p>
          Ohne <code>--confirmed</code>: endet vor Routerbau und Netzwerkzugriff.
        </p>
      </div>

      <div className="benchmark-privacy">
        <ShieldCheck weight="regular" aria-hidden="true" />
        <div>
          <p>{benchmarkStatus.privacyNotice}</p>
          <p>{benchmarkStatus.trustNotice}</p>
        </div>
      </div>

      <div className="benchmark-action-row">
        <button
          type="button"
          disabled
          aria-describedby="benchmark-disabled-reason"
          title="Keine sichere Benchmark-API-Route vorhanden"
        >
          <Play weight="fill" aria-hidden="true" />
          Benchmark starten
        </button>
        <span id="benchmark-disabled-reason">
          Deaktiviert: Es existiert bewusst keine ausführende Benchmark-API-Route.
        </span>
      </div>
    </section>
  );
}
