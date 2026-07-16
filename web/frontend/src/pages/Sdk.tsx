import { Link } from "react-router-dom";
import { BRAND, PROTOCOL } from "../brand";

const LANGS = [
  {
    name: "Python",
    status: "available",
    install: "pip install narna",
    desc: "Reference client: Constitution, Identity, Passport, VAP, Certification, CLI.",
    links: [
      { to: "/docs/install", label: "Install" },
      { to: "/docs/quickstart", label: "Quickstart" },
    ],
  },
  {
    name: "TypeScript",
    status: "planned",
    install: "npm install @narna/sdk",
    desc: "Same Constitution contracts for browser and Node.",
    links: [],
  },
  {
    name: "Go",
    status: "planned",
    install: "go get github.com/hanyangkai/narna-go",
    desc: "Server-side Constitution + Evidence bindings.",
    links: [],
  },
  {
    name: "Rust",
    status: "planned",
    install: "cargo add narna",
    desc: "High-assurance evidence hashing and verify.",
    links: [],
  },
];

export default function Sdk() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Reference SDK</p>
        <h1>Try the Constitution Layer locally</h1>
        <p>
          The SDK is a <strong>virus entry</strong> — not the strategic USP. Specs are the source of truth.
          Use it to load <code>constitution.yaml</code>, issue identity, prove actions, and certify.
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <div className="install-block" style={{ maxWidth: 440 }}>
          <label>Python (available now)</label>
          <div className="install-cmd">
            <code>{PROTOCOL.install}</code>
            <Link to="/docs/install" className="btn btn-primary" style={{ flexShrink: 0 }}>
              Install
            </Link>
          </div>
        </div>
        <p style={{ color: "var(--muted)", marginTop: "1rem", maxWidth: 560 }}>
          {BRAND.contrast}
        </p>
      </section>

      <section className="section">
        <h2>Languages</h2>
        <div className="feature-grid">
          {LANGS.map((lang) => (
            <div key={lang.name} className="card">
              <h3 style={{ margin: "0 0 0.25rem" }}>{lang.name}</h3>
              <div className={`status status-${lang.status}`} style={{ marginBottom: "0.75rem" }}>
                {lang.status === "available" ? "Available" : "Planned"}
              </div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem", margin: "0 0 0.75rem" }}>
                {lang.desc}
              </p>
              <pre className="code-block mono" style={{ margin: "0 0 0.75rem", fontSize: "0.8rem" }}>
                {lang.install}
              </pre>
              {lang.links.map((l) => (
                <Link key={l.to} to={l.to} style={{ marginRight: "1rem" }}>
                  {l.label} →
                </Link>
              ))}
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>CLI</h2>
        <pre className="code-block mono">{`narna constitution   # validate charter
narna init           # workspace + identity
narna run --vap      # prove actions
narna passport       # public trust view
narna certify        # Verified by NARNA
narna doctor --full  # conformance`}</pre>
      </section>

      <section className="section">
        <h2>Compatibility first</h2>
        <p className="section-desc">
          NARNA sits above frameworks — wrap, don&apos;t replace.
        </p>
        <ul className="enterprise-list">
          <li>OpenTelemetry</li>
          <li>MCP</li>
          <li>OpenAI Agents SDK</li>
          <li>LangGraph</li>
          <li>CrewAI</li>
          <li>OpenShell</li>
        </ul>
        <Link to="/docs/compatibility" className="btn btn-secondary" style={{ marginTop: "1rem" }}>
          Compatibility guide →
        </Link>
      </section>
    </div>
  );
}
