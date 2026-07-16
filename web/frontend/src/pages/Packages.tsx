import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";

type PackageRow = {
  packageId: string;
  name: string;
  version: string;
  provider: string;
  packageKind: string;
  license: string;
  disclaimer: string;
  packageHash: string;
  spec: Record<string, unknown>;
  stars: number;
  downloads: number;
  publishedAt: string;
};

export default function Packages() {
  const [packages, setPackages] = useState<PackageRow[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      const res = await fetch(`${API_BASE}/v1/packages?${params}`);
      if (!res.ok) throw new Error(await res.text());
      setPackages(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPackages([]);
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
        <p className="pill-label">Constitution Marketplace</p>
        <h1>Governance Packages</h1>
        <p>
          Publish constitutions and compliance packs — NARNA loads them via the Constitution Runtime.
          <code> narna package pull eu-ai-act</code>
        </p>
      </header>

      <div className="console-bar">
        <label>
          Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="provider or id" />
        </label>
        <button type="button" className="btn btn-primary" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Search"}
        </button>
      </div>

      {error && (
        <div className="error">
          {error}
          <p style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
            Seed locally: <code>narna package publish ./specs/examples/packages/eu-ai-act.yaml --local</code>
          </p>
        </div>
      )}

      <section className="section" style={{ paddingTop: "1rem", borderTop: "none" }}>
        <h2>Published packages</h2>
        {packages.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>
            No packages yet. Stubs live in <code>specs/examples/packages/</code> (community demos — not official
            endorsements).
          </p>
        ) : (
          <div className="card" style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Package</th>
                  <th>Provider</th>
                  <th>Kind</th>
                  <th>Version</th>
                  <th>License</th>
                </tr>
              </thead>
              <tbody>
                {packages.map((p) => (
                  <tr key={p.packageId}>
                    <td>
                      <strong>{p.name}</strong>
                      <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{p.packageId}</div>
                      {p.disclaimer && (
                        <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: 4 }}>
                          {p.disclaimer}
                        </div>
                      )}
                    </td>
                    <td>{p.provider}</td>
                    <td>{p.packageKind}</td>
                    <td>{p.version}</td>
                    <td>{p.license}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section">
        <h2>CLI</h2>
        <pre className="code-block">{`narna package search
narna package publish ./specs/examples/packages/eu-ai-act.yaml
narna package pull eu-ai-act --version 1.0.0
narna governance execute --action biometric.surveillance`}</pre>
      </section>
    </div>
  );
}
