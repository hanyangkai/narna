import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DEFAULT_DEV_KEY, fetchRuns, healthCheck, type RunSummary } from "../api";

function stateBadge(state: string) {
  if (state === "Completed") return "badge badge-ok";
  if (state === "Failed") return "badge badge-fail";
  if (state === "AwaitingInput") return "badge badge-wait";
  return "badge";
}

export default function Console() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    healthCheck().then(setApiOk);
  }, []);

  async function load() {
    setError(null);
    localStorage.setItem("uap_api_key", apiKey);
    try {
      const data = await fetchRuns(apiKey);
      setRuns(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setRuns([]);
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
        <p>Hosted audit dashboard. Optional — NARNA SDK runs fully local without this.</p>
      </header>
      <p style={{ color: "var(--muted)" }}>
        Hosted runs, audit trail, proof bundles. API status:{" "}
        {apiOk === null ? "…" : apiOk ? "online" : "offline"}
        {" · "}
        <Link to="/billing">Manage billing</Link>
      </p>
      <div className="console-bar">
        <label>
          API Key
          <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="mono" />
        </label>
        <button type="button" className="btn btn-primary" onClick={load}>
          Refresh
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Agent</th>
            <th>State</th>
            <th>Trust</th>
            <th>Events</th>
            <th>Updated</th>
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
              <td>{r.agentName || r.agentId}</td>
              <td>
                <span className={stateBadge(r.state)}>{r.state}</span>
              </td>
              <td>{r.trustScore != null ? r.trustScore.toFixed(2) : "—"}</td>
              <td>{r.eventCount}</td>
              <td className="mono" style={{ fontSize: "0.8rem" }}>
                {r.updatedAt.slice(0, 19)}
              </td>
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
    </section>
    </div>
  );
}
