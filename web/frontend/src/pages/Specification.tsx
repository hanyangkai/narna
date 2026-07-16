import { Link } from "react-router-dom";

const SPECS = [
  { id: "uap-core", name: "UAP-Core", desc: "AgentSpec, Identity, Passport, Capability, Permission, Policy, Event model", path: "uap-core/SPEC.md" },
  { id: "uap-execution", name: "UAP-Execution", desc: "Run lifecycle, tool contract, permission gating, adapters", path: "uap-execution/SPEC.md" },
  { id: "uap-evidence", name: "UAP-Evidence", desc: "Evidence object, hashing, provenance, retention", path: "uap-evidence/SPEC.md" },
  { id: "vap", name: "VAP", desc: "Verify, Audit, Prove, ProofBundle, Trust Score", path: "vap/SPEC.md" },
  { id: "uap-export", name: "UAP-Export", desc: "Cloud telemetry export protocol (OTLP-like)", path: "uap-export/SPEC.md" },
];

const SCHEMAS = [
  "agent-spec.schema.json",
  "identity.schema.json",
  "passport.schema.json",
  "event.schema.json",
  "tool.schema.json",
  "evidence.schema.json",
  "policy-decision.schema.json",
  "proof-bundle.schema.json",
  "trust-score.schema.json",
];

const SECTIONS = [
  "Identity",
  "Capability",
  "Permission",
  "Policy",
  "Evidence",
  "Execution",
  "Passport",
];

export default function Specification() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Normative</p>
        <h1>UAP Specification</h1>
        <p>
          Version 0.1 — Draft. The open protocol behind NARNA. MIT licensed. The contract that makes agent execution verifiable and governable.
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <p className="section-label">Design axiom</p>
        <div className="pipeline">
          {["Identity", "Policy", "Action", "Evidence", "Trust"].map((s, i, arr) => (
            <span key={s} style={{ display: "contents" }}>
              <div className="pipeline-step">{s}</div>
              {i < arr.length - 1 && <span className="pipeline-arrow">→</span>}
            </span>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>Specification documents</h2>
        <table className="spec-table">
          <thead>
            <tr>
              <th>Spec</th>
              <th>Scope</th>
            </tr>
          </thead>
          <tbody>
            {SPECS.map((s) => (
              <tr key={s.id}>
                <td><strong>{s.name}</strong></td>
                <td>{s.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ marginTop: "1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
          Full text in repository: <code>specs/</code>
        </p>
      </section>

      <section className="section">
        <h2>Core sections</h2>
        <div className="feature-grid">
          {SECTIONS.map((s) => (
            <div key={s} className="card feature-card">
              <h3>{s}</h3>
              <p>Defined in UAP-Core and related normative documents.</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>JSON Schemas</h2>
        <p className="section-desc">Machine-readable contracts for validation and interoperability.</p>
        <div className="card">
          <ul style={{ margin: 0, paddingLeft: "1.25rem", columns: 2 }}>
            {SCHEMAS.map((s) => (
              <li key={s} className="mono" style={{ fontSize: "0.85rem", marginBottom: "0.35rem" }}>{s}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section">
        <h2>Conformance</h2>
        <p>
          A runtime is <strong>UAP-conformant</strong> if it implements UAP-Core, UAP-Execution, and UAP-Evidence.
          A runtime is <strong>VAP-conformant</strong> if it additionally implements the VAP Spec (Verify → Audit → Prove).
        </p>
        <pre className="code-block mono">{`uap doctor --full   # local conformance check`}</pre>
      </section>

      <section className="section">
        <h2>RFC roadmap</h2>
        <p className="section-desc">
          v0.1 is a draft for community review. Future versions will follow an RFC process for breaking changes.
        </p>
        <Link to="/docs/quickstart" className="btn btn-primary">Implement the spec →</Link>
      </section>
    </div>
  );
}
