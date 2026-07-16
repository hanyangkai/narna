import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";

type PluginRow = {
  pluginId: string;
  name: string;
  version: string;
  license: string;
  spec: Record<string, unknown>;
  stars: number;
  downloads: number;
  publishedAt: string;
};

export default function Plugins() {
  const [plugins, setPlugins] = useState<PluginRow[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      const res = await fetch(`${API_BASE}/v1/plugins?${params}`);
      if (!res.ok) throw new Error(await res.text());
      setPlugins(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPlugins([]);
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
        <p className="pill-label">Plugins</p>
        <h1>Plugin Registry</h1>
        <p>
          Extend agents with community plugins — never replace the host. Publish with{" "}
          <code>narna plugin publish ./plugins/narna-slack</code>.
        </p>
      </header>

      <div className="console-bar">
        <label>
          Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="name or id" />
        </label>
        <button type="button" className="btn btn-primary" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Search"}
        </button>
      </div>

      {error && (
        <div className="error">
          {error}
          <p style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
            Start API, then: <code>narna plugin publish ./plugins/narna-slack</code>
          </p>
        </div>
      )}

      <section className="section" style={{ paddingTop: "1rem", borderTop: "none" }}>
        <h2>Published plugins</h2>
        {plugins.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>
            No plugins yet. Copy <code>plugins/TEMPLATE</code>, then publish.
          </p>
        ) : (
          <div className="card" style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Plugin</th>
                  <th>Version</th>
                  <th>License</th>
                  <th>Extends</th>
                  <th>Stars</th>
                </tr>
              </thead>
              <tbody>
                {plugins.map((p) => {
                  const extendsList = Array.isArray(p.spec?.extends)
                    ? (p.spec.extends as string[]).join(", ")
                    : "—";
                  return (
                    <tr key={p.pluginId}>
                      <td>
                        <strong>{p.name}</strong>
                        <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{p.pluginId}</div>
                      </td>
                      <td>{p.version}</td>
                      <td>{p.license}</td>
                      <td>{extendsList}</td>
                      <td>{p.stars}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section">
        <h2>CLI</h2>
        <pre className="code-block">{`narna plugin list
narna plugin publish ./plugins/narna-slack
narna plugin attach ./plugins/narna-slack --spec agent.yaml`}</pre>
      </section>
    </div>
  );
}
