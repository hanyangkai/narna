import { Link } from "react-router-dom";
import { BRAND } from "../brand";

const SPECS = [
  {
    id: "constitution",
    name: "Constitution",
    desc: "constitution.yaml — identity, capability, permission, policy, evidence, trust",
    path: "constitution/SPEC.md",
  },
  {
    id: "identity",
    name: "Universal Identity",
    desc: "Portable birth record for Agent, Tool, MCP, Workflow, Prompt, Dataset, …",
    path: "identity/SPEC.md",
  },
  {
    id: "uap-core",
    name: "UAP-Core",
    desc: "AgentSpec, Passport, Capability, Permission, Policy, Event model",
    path: "uap-core/SPEC.md",
  },
  {
    id: "uap-evidence",
    name: "UAP-Evidence",
    desc: "Evidence object, hashing, provenance, retention",
    path: "uap-evidence/SPEC.md",
  },
  {
    id: "vap",
    name: "VAP",
    desc: "Verify, Audit, Prove, ProofBundle, Trust Score",
    path: "vap/SPEC.md",
  },
  {
    id: "uap-execution",
    name: "UAP-Execution",
    desc: "Reference / adapter lifecycle (not the USP)",
    path: "uap-execution/SPEC.md",
  },
];

const SCHEMAS = [
  "constitution.schema.json",
  "universal-identity.schema.json",
  "agent-spec.schema.json",
  "identity.schema.json",
  "passport.schema.json",
  "event.schema.json",
  "evidence.schema.json",
  "policy-decision.schema.json",
  "proof-bundle.schema.json",
  "trust-score.schema.json",
];

const SECTIONS = [
  "Constitution",
  "Identity",
  "Capability",
  "Permission",
  "Policy",
  "Evidence",
  "Trust",
  "Passport",
  "Certification",
];

export default function Specification() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Normative · Spec first</p>
        <h1>NARNA Specification</h1>
        <p>
          Version 0.1 — Draft. The Constitution Layer contracts: who AI is, what it may do, and why
          others can trust it. MIT licensed. Frameworks execute; this layer governs.
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <p className="section-label">Design axiom</p>
        <div className="pipeline">
          {["Identity", "Capability", "Policy", "Evidence", "Trust"].map((s, i, arr) => (
            <span key={s} style={{ display: "contents" }}>
              <div className="pipeline-step">{s}</div>
              {i < arr.length - 1 && <span className="pipeline-arrow">→</span>}
            </span>
          ))}
        </div>
        <p style={{ color: "var(--muted)", marginTop: "1rem", maxWidth: 640 }}>
          {BRAND.contrast}
        </p>
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
                <td>
                  <strong>{s.name}</strong>
                  <div className="mono" style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
                    specs/{s.path}
                  </div>
                </td>
                <td>{s.desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="section">
        <h2>Core sections</h2>
        <div className="feature-grid">
          {SECTIONS.map((s) => (
            <div key={s} className="card feature-card">
              <h3>{s}</h3>
              <p>Part of the Constitution Layer stack.</p>
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
              <li key={s} className="mono" style={{ fontSize: "0.85rem", marginBottom: "0.35rem" }}>
                {s}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section">
        <h2>Conformance</h2>
        <p>
          <strong>Constitution-conformant</strong> — load and enforce <code>constitution.yaml</code>.
          <br />
          <strong>VAP-conformant</strong> — ProofBundle + Trust Score + offline verify.
          <br />
          <strong>Certified</strong> — NARNA Certification levels against Constitution + Evidence.
        </p>
        <pre className="code-block mono">{`narna constitution
narna doctor --full
narna certify --vap --local`}</pre>
      </section>

      <section className="section">
        <h2>Start reading</h2>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <Link to="/docs/what-is-narna" className="btn btn-primary">
            What is NARNA?
          </Link>
          <Link to="/docs/constitution" className="btn btn-secondary">
            Constitution guide
          </Link>
        </div>
      </section>
    </div>
  );
}
