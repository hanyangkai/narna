import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  DEFAULT_DEV_KEY,
  fetchRuns,
  fetchSessions,
  healthCheck,
  type RunSummary,
  type SessionSummary,
} from "../api";

function stateBadge(state: string) {
  if (state === "Completed" || state === "closed") return "badge badge-ok";
  if (state === "Failed" || state === "terminated") return "badge badge-fail";
  if (state === "AwaitingInput" || state === "open") return "badge badge-wait";
  return "badge";
}

export default function Console() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY);
  const [tab, setTab] = useState<"sessions" | "runs">("sessions");
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    healthCheck().then(setApiOk);
  }, []);

  async function load() {
    setError(null);
    localStorage.setItem("uap_api_key", apiKey);
    try {
      const [r, s] = await Promise.all([fetchRuns(apiKey), fetchSessions(apiKey)]);
      setRuns(r);
      setSessions(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setRuns([]);
      setSessions([]);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="layout-wide">
      <section>
        <header className="page-header" style={{ paddingTop: "1rem" }}>
          <p className="pill-label">Cloud</p>
          <h1>NARNA Cloud Console</h1>
          <p>
            Governance Sessions + Execution Graphs. Metered by GU — not agent count. API:{" "}
            {apiOk === null ? "…" : apiOk ? "online" : "offline"}
            {" · "}
            <Link to="/billing">Billing</Link>
          </p>
        </header>
        <div className="console-bar">
          <label>
            API Key
            <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="mono" />
          </label>
          <button type="button" className="btn btn-primary" onClick={load}>
            Refresh
          </button>
        </div>
        <div className="console-tabs" style={{ display: "flex", gap: "0.5rem", margin: "1rem 0" }}>
          <button
            type="button"
            className={`btn ${tab === "sessions" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setTab("sessions")}
          >
            Sessions
          </button>
          <button
            type="button"
            className={`btn ${tab === "runs" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setTab("runs")}
          >
            Runs
          </button>
        </div>
        {error && <div className="error">{error}</div>}

        {tab === "sessions" && (
          <table>
            <thead>
              <tr>
                <th>Session</th>
                <th>Agent</th>
                <th>State</th>
                <th>GU</th>
                <th>Runs</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.sessionId}>
                  <td>
                    <Link to={`/console/sessions/${s.sessionId}`} className="mono">
                      {s.sessionId.slice(0, 22)}…
                    </Link>
                  </td>
                  <td>{s.logicalAgentId}</td>
                  <td>
                    <span className={stateBadge(s.state)}>{s.state}</span>
                  </td>
                  <td>{s.totalGu}</td>
                  <td>{s.runCount}</td>
                  <td className="mono" style={{ fontSize: "0.8rem" }}>
                    {s.createdAt.slice(0, 19)}
                  </td>
                </tr>
              ))}
              {sessions.length === 0 && !error && (
                <tr>
                  <td colSpan={6} style={{ color: "var(--muted)", padding: "2rem" }}>
                    No sessions yet. Push a run with ExecutionUnitStarted events.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {tab === "runs" && (
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Session</th>
                <th>Agent</th>
                <th>State</th>
                <th>GU</th>
                <th>Events</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.runId}>
                  <td>
                    <Link to={`/console/runs/${r.runId}`} className="mono">
                      {r.runId.slice(0, 20)}…
                    </Link>
                  </td>
                  <td>
                    {r.sessionId ? (
                      <Link to={`/console/sessions/${r.sessionId}`} className="mono">
                        {r.sessionId.slice(0, 14)}…
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{r.agentName || r.agentId}</td>
                  <td>
                    <span className={stateBadge(r.state)}>{r.state}</span>
                  </td>
                  <td>{r.totalGu ?? 0}</td>
                  <td>{r.eventCount}</td>
                </tr>
              ))}
              {runs.length === 0 && !error && (
                <tr>
                  <td colSpan={6} style={{ color: "var(--muted)", padding: "2rem" }}>
                    No runs yet. Run <code>uap push --run &lt;id&gt;</code> to sync.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
