import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DEFAULT_DEV_KEY, fetchRun, type RunDetail } from "../api";

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const apiKey = localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY;
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    fetchRun(apiKey, runId)
      .then(setRun)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [runId, apiKey]);

  if (error) return <div className="error">{error}</div>;
  if (!run) return <p>Loading…</p>;

  return (
    <section>
      <p>
        <Link to="/console">← Console</Link>
      </p>
      <h1 className="mono">{run.runId}</h1>
      <p>
        {run.agentName} · <span className="badge badge-ok">{run.state}</span>
        {run.trustScore != null && <> · Trust {run.trustScore.toFixed(2)}</>}
      </p>
      <p className="mono" style={{ fontSize: "0.75rem", color: "var(--muted)", wordBreak: "break-all" }}>
        tip: {run.tipHash}
      </p>
      <h2>Event timeline</h2>
      <ul className="timeline">
        {run.events.map((e) => (
          <li key={e.eventId}>
            <span className="type">{e.eventType}</span>
            <span style={{ color: "var(--muted)", marginLeft: "0.5rem" }}>#{e.sequence}</span>
            <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{e.ts}</div>
            {e.eventType === "PolicyEvaluated" && (
              <div className="mono" style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
                {(e.payload as { decision?: { decision?: string } }).decision?.decision}
              </div>
            )}
            {e.eventType === "ActionExecuted" && (
              <div className="mono" style={{ fontSize: "0.75rem", marginTop: "0.25rem" }}>
                {JSON.stringify((e.payload as { tool?: string }).tool)}
              </div>
            )}
          </li>
        ))}
      </ul>
      {run.proofBundle && (
        <>
          <h2>Proof bundle</h2>
          <pre className="card mono" style={{ overflow: "auto", maxHeight: 300, fontSize: "0.7rem" }}>
            {JSON.stringify(run.proofBundle, null, 2)}
          </pre>
        </>
      )}
    </section>
  );
}
