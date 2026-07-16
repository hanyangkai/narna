import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "";

type Row = {
  vendor: string;
  score: number;
  breakdown?: Record<string, number>;
  notes?: string;
};

export default function Benchmark() {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/v1/benchmark/governance`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data) => setRows(data.rows || []))
      .catch((e) => {
        setError(e instanceof Error ? e.message : String(e));
        // offline fallback seed
        setRows([
          { vendor: "Anthropic", score: 0.98, notes: "Strong policy culture" },
          { vendor: "OpenAI", score: 0.96, notes: "Agents SDK + OTel" },
          { vendor: "Google", score: 0.94, notes: "Gemini / ADK" },
          { vendor: "LangGraph", score: 0.92, notes: "narna-langgraph" },
          { vendor: "CrewAI", score: 0.9, notes: "narna-crewai" },
        ]);
      });
  }, []);

  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Governance Benchmark</p>
        <h1>Not LLM MMLU — compliance posture</h1>
        <p>
          Rank stacks on identity, permission, evidence, policy, and certification.
          Use this to compare hosts you wrap — not to crown a single model.
        </p>
      </header>

      {error && (
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          API offline — showing reference board. Start backend for live merge with local workspace scores.
        </p>
      )}

      <div className="card" style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Vendor / Stack</th>
              <th>Score</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.vendor}-${i}`}>
                <td>{i + 1}</td>
                <td>
                  <strong>{r.vendor}</strong>
                </td>
                <td>{Number(r.score).toFixed(2)}</td>
                <td style={{ color: "var(--muted)" }}>{r.notes || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p style={{ marginTop: "1.5rem" }}>
        <Link to="/docs/borrow-the-wave" className="btn btn-secondary">
          Strategy →
        </Link>
        <code style={{ marginLeft: "1rem" }}>narna benchmark --governance</code>
      </p>
    </div>
  );
}
