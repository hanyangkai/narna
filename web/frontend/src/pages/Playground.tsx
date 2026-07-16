import { useState } from "react";
import { Link } from "react-router-dom";

const DEFAULT_MANIFEST = `apiVersion: narna.ai/v1alpha1
kind: Manifest
metadata:
  name: Research Agent
  owner: local
identity:
  id: research-agent
  version: "0.1.0"
capabilities:
  - browser.read
  - research.query
permissions:
  - name: browser.read
    mode: allow
governance:
  package: eu-ai-act@1.0.0
runtime:
  narna: true
passport:
  enabled: true
trust:
  enabled: true
  minimum_score: 0.7
`;

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function Playground() {
  const [yaml, setYaml] = useState(DEFAULT_MANIFEST);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function validate() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/v1/playground/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manifest: yaml }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.error || "Validation failed");
      }
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Playground</p>
        <h1>Try narna.yaml in the browser</h1>
        <p>
          Validate and preview governance compilation — no install required. Edit the manifest, click Validate,
          see constitution preview and dimension scores.
        </p>
      </header>

      <section className="section two-col" style={{ paddingTop: 0, borderTop: "none" }}>
        <div>
          <label className="mono" style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            narna.yaml
          </label>
          <textarea
            value={yaml}
            onChange={(e) => setYaml(e.target.value)}
            className="code-block mono"
            style={{
              width: "100%",
              minHeight: 420,
              marginTop: "0.5rem",
              fontSize: "0.8rem",
              resize: "vertical",
            }}
            spellCheck={false}
          />
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem", flexWrap: "wrap" }}>
            <button type="button" className="btn btn-primary" onClick={validate} disabled={loading}>
              {loading ? "Validating…" : "Validate"}
            </button>
            <Link to="/docs/install" className="btn btn-secondary">
              Install SDK →
            </Link>
          </div>
        </div>
        <div>
          <h3>Result</h3>
          {error && (
            <pre className="code-block mono" style={{ color: "var(--danger, #b91c1c)" }}>
              {error}
            </pre>
          )}
          {result && (
            <pre className="code-block mono" style={{ fontSize: "0.78rem", maxHeight: 520, overflow: "auto" }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
          {!error && !result && (
            <p style={{ color: "var(--muted)" }}>Click Validate to compile manifest and preview NARNA Score dimensions.</p>
          )}
        </div>
      </section>
    </div>
  );
}
