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
        <p className="pill-label">Benchmarks</p>
        <h1>Decision quality — not model MMLU</h1>
        <p>
          Score whether an agent should ACT, REVIEW, or REJECT. Governance posture board is secondary —
          we never invent Decision Benchmark accuracy for marketing.
        </p>
      </header>

      <section className="section" style={{ marginBottom: "2.5rem" }}>
        <h2>Decision Benchmark v0</h2>
        <p className="section-desc">
          55 open scenarios (research, code, procurement, legal, compliance, finance). Run locally with
          BYOK-ready CLI — publish your own results via PR.
        </p>
        <pre className="code-block">{`narna benchmark run --agent mock
narna benchmark run --category legal --verbose`}</pre>
        <p style={{ color: "var(--muted)", marginTop: "0.75rem" }}>
          Docs: <code>benchmark/README.md</code> · regenerate:{" "}
          <code>python scripts/gen_decision_benchmark.py</code>
        </p>
        <div className="land-cta" style={{ marginTop: "1rem" }}>
          <Link className="btn btn-primary" to="/ask">
            Try the agent
          </Link>
          <a
            className="btn btn-secondary"
            href="https://github.com/hanyangkai/narna/tree/main/benchmark"
            target="_blank"
            rel="noreferrer"
          >
            Scenarios on GitHub
          </a>
        </div>
      </section>

      <section className="section">
        <h2>Governance posture board</h2>
        <p className="section-desc">
          Rank stacks on identity, permission, evidence, policy, and certification — compare hosts you
          wrap, not crown a single model.
        </p>

        {error && (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            API offline — showing reference board. Start backend for live workspace scores.
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
          <code>narna benchmark --governance</code>
        </p>
      </section>
    </div>
  );
}
