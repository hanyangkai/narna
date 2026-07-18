import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DEFAULT_DEV_KEY, fetchSession, type SessionDetail } from "../api";

function GraphView({ units }: { units: Array<Record<string, unknown>> }) {
  if (!units.length) {
    return <p style={{ color: "var(--muted)" }}>No execution units yet.</p>;
  }
  return (
    <div className="session-graph">
      {units.map((u) => {
        const id = String(u.unitId || "");
        const kind = String(u.unitKind || "tool");
        const parent = u.parentUnitId ? String(u.parentUnitId) : null;
        const gu = Number(u.guCost || 1);
        const label = String(u.label || u.toolName || kind);
        return (
          <div key={id} className={`session-node kind-${kind}`}>
            <div className="session-node-kind">{kind}</div>
            <div className="session-node-label">{label}</div>
            <div className="session-node-meta mono">
              {id.slice(0, 18)}… · {gu} GU
              {parent ? ` · ← ${parent.slice(0, 12)}…` : " · root"}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function SessionDetailPage() {
  const { sessionId } = useParams();
  const [apiKey] = useState(() => localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY);
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    fetchSession(apiKey, sessionId)
      .then(setSession)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [apiKey, sessionId]);

  if (error) {
    return (
      <div className="layout-wide">
        <Link to="/console">← Console</Link>
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="layout-wide">
        <p style={{ color: "var(--muted)" }}>Loading session…</p>
      </div>
    );
  }

  return (
    <div className="layout-wide">
      <p>
        <Link to="/console">← Console</Link>
      </p>
      <header className="page-header" style={{ paddingTop: "0.5rem" }}>
        <p className="pill-label">Governance Session</p>
        <h1 className="mono" style={{ fontSize: "1.4rem" }}>
          {session.sessionId}
        </h1>
        <p>
          Agent <strong>{session.logicalAgentId}</strong> · {session.totalGu} GU ·{" "}
          <span className="badge">{session.state}</span>
          {session.terminateReason ? ` · ${session.terminateReason}` : ""}
        </p>
      </header>

      <section className="section" style={{ borderTop: "none", paddingTop: "0.5rem" }}>
        <h2>Execution Graph</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          Logical Agent = identity. Each node = Execution Unit (1 GU by default). Spawn trees cannot cheat.
        </p>
        <GraphView units={session.units} />
      </section>

      <section className="section">
        <h2>Runs in session</h2>
        <table>
          <thead>
            <tr>
              <th>Run</th>
              <th>Agent</th>
              <th>State</th>
              <th>GU</th>
            </tr>
          </thead>
          <tbody>
            {session.runs.map((r) => (
              <tr key={r.runId}>
                <td>
                  <Link to={`/console/runs/${r.runId}`} className="mono">
                    {r.runId.slice(0, 20)}…
                  </Link>
                </td>
                <td>{r.agentName || r.agentId}</td>
                <td>{r.state}</td>
                <td>{r.totalGu ?? 0}</td>
              </tr>
            ))}
            {session.runs.length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: "var(--muted)" }}>
                  No runs linked yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
