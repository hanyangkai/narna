import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "";

type AgentRow = {
  agentId: string;
  name: string;
  version: string;
  creator: string;
  category: string;
  capabilities: string[];
  trustScore: number | null;
  stars: number;
  downloads: number;
  executions: number;
  publishedAt: string;
  passportUrl: string;
  verified?: boolean;
  badge?: string | null;
};

export default function Registry() {
  const [agents, setAgents] = useState<AgentRow[]>([]);
  const [trending, setTrending] = useState<AgentRow[]>([]);
  const [category, setCategory] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      if (q) params.set("q", q);
      const [listRes, trendRes] = await Promise.all([
        fetch(`${API_BASE}/v1/registry/agents?${params}`),
        fetch(`${API_BASE}/v1/registry/trending${category ? `?category=${encodeURIComponent(category)}` : ""}`),
      ]);
      if (!listRes.ok) throw new Error(await listRes.text());
      if (!trendRes.ok) throw new Error(await trendRes.text());
      setAgents(await listRes.json());
      setTrending(await trendRes.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setAgents([]);
      setTrending([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Registry</p>
        <h1>Agent Registry</h1>
        <p>
          Discover agents with portable identity, constitution, and trust.
          Publish with <code>narna publish</code>, certify with <code>narna certify</code>.
        </p>
      </header>

      <div className="console-bar">
        <label>
          Category
          <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="trade, code, research…" />
        </label>
        <label>
          Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="name or creator" />
        </label>
        <button type="button" className="btn btn-primary" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Search"}
        </button>
      </div>

      {error && (
        <div className="error">
          {error}
          <p style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
            Start API: <code>uvicorn app.main:app --port 8000</code> then publish an agent.
          </p>
        </div>
      )}

      <section className="section" style={{ paddingTop: "1rem", borderTop: "none" }}>
        <h2>Trending</h2>
        <AgentTable rows={trending} empty="No trending agents yet." />
      </section>

      <section className="section">
        <h2>All published</h2>
        <AgentTable rows={agents} empty="Registry empty — run narna publish." />
      </section>
    </div>
  );
}

function AgentTable({ rows, empty }: { rows: AgentRow[]; empty: string }) {
  if (rows.length === 0) {
    return <p style={{ color: "var(--muted)" }}>{empty}</p>;
  }
  return (
    <div className="card" style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Agent</th>
            <th>Category</th>
            <th>Trust</th>
            <th>Badge</th>
            <th>Stars</th>
            <th>Downloads</th>
            <th>Passport</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.agentId}>
              <td>
                <strong>{a.name}</strong>
                <div className="mono" style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
                  {a.agentId}
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                  v{a.version} · {a.creator}
                </div>
              </td>
              <td>{a.category}</td>
              <td>{a.trustScore != null ? a.trustScore.toFixed(2) : "—"}</td>
              <td>
                {a.verified ? (
                  <span className="badge badge-ok">{a.badge || "Verified by NARNA"}</span>
                ) : (
                  <span style={{ color: "var(--muted)" }}>—</span>
                )}
              </td>
              <td>{a.stars}</td>
              <td>{a.downloads}</td>
              <td>
                <Link to={`/passport/${a.agentId}`}>View →</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
