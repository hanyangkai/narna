import { Link } from "react-router-dom";

const FEATURES = [
  "Self Hosted",
  "Cloud",
  "RBAC",
  "SSO",
  "Compliance",
  "SOC2",
  "Audit",
  "On-Premise",
];

export default function Enterprise() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Enterprise</p>
        <h1>Self-host first. Cloud when you need it.</h1>
        <p>
          Banks, insurance, and government need portable identity, policy, and proof — not another
          black-box agent runtime. NARNA is the Constitution Layer your security team can audit.
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <div className="two-col">
          <div>
            <h2>Why enterprises choose NARNA</h2>
            <p>
              Not a closed platform. An open Constitution Layer: who each AI entity is, what it may do,
              and why auditors can trust it — across OpenAI, Claude, Gemini, and any orchestrator.
            </p>
            <ul style={{ color: "var(--muted)", paddingLeft: "1.25rem" }}>
              <li>Universal Identity — agents, tools, MCP servers, workflows</li>
              <li>Constitution / policy — deny-by-default permissions</li>
              <li>Evidence + VAP — cryptographic proof, not just logs</li>
              <li>Certification — Verified by NARNA · fleet governance</li>
              <li>Self-host — <code>docker compose up</code> on your infrastructure</li>
            </ul>
          </div>
          <div className="card">
            <pre className="code-block mono" style={{ margin: 0 }}>{`# Self-host on your VPS
docker compose up --build

# Or Hetzner + Coolify
# See docs/SELF-HOST.md`}</pre>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Enterprise capabilities</h2>
        <ul className="enterprise-list">
          {FEATURES.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </section>

      <section className="section">
        <h2>Deployment options</h2>
        <div className="feature-grid">
          <div className="card feature-card">
            <h3>On-Premise</h3>
            <p>Docker Compose on your VPS or data center. Postgres + Redis + API + Dashboard.</p>
          </div>
          <div className="card feature-card">
            <h3>Private Cloud</h3>
            <p>Hosted in your AWS/GCP/Azure account. We provide the Helm chart and runbook.</p>
          </div>
          <div className="card feature-card">
            <h3>NARNA Cloud</h3>
            <p>Managed telemetry when you don&apos;t want to operate infrastructure.</p>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Contact</h2>
        <p className="section-desc">
          Enterprise pilots, compliance reviews, and custom deployment architecture.
        </p>
        <a href="mailto:enterprise@narna.ai" className="btn btn-primary">
          Contact Enterprise
        </a>
        <span style={{ margin: "0 0.75rem" }} />
        <Link to="/pricing" className="btn btn-secondary">
          View pricing
        </Link>
      </section>
    </div>
  );
}
