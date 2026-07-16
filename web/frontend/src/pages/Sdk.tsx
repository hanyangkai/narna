import { Link } from "react-router-dom";

const LANGS = [
  {
    name: "Python",
    status: "available",
    install: "pip install uap",
    desc: "Reference SDK. Agent, Policy, Evidence, VAP pipeline, CLI.",
    links: [
      { to: "/docs/install", label: "Install" },
      { to: "/docs/quickstart", label: "Quickstart" },
    ],
  },
  {
    name: "TypeScript",
    status: "planned",
    install: "npm install @uap/sdk",
    desc: "Browser and Node.js agents. Planned for v0.2.",
    links: [],
  },
  {
    name: "Go",
    status: "planned",
    install: "go get github.com/uap-standard/uap-go",
    desc: "High-performance runtime for server-side agents.",
    links: [],
  },
  {
    name: "Rust",
    status: "planned",
    install: "cargo add uap-sdk",
    desc: "Systems-level agent runtime with zero-copy evidence.",
    links: [],
  },
  {
    name: "Java",
    status: "planned",
    install: "implementation 'dev.uap:uap-sdk'",
    desc: "Enterprise JVM integration.",
    links: [],
  },
];

export default function Sdk() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">SDK</p>
        <h1>Install. Wrap. Prove.</h1>
        <p>
          NARNA SDK implements the UAP protocol. Cloud is optional. Start with Python — other languages follow the same specification.
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <div className="install-block" style={{ maxWidth: 400 }}>
          <label>Python (available now)</label>
          <div className="install-cmd">
            <code>pip install uap</code>
            <Link to="/docs/install" className="btn btn-primary" style={{ flexShrink: 0 }}>
              Install
            </Link>
          </div>
        </div>
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
              <p style={{ color: "var(--muted)", fontSize: "0.9rem", margin: "0 0 0.75rem" }}>{lang.desc}</p>
              <pre className="code-block mono" style={{ margin: "0 0 0.75rem", fontSize: "0.8rem" }}>{lang.install}</pre>
              {lang.links.map((l) => (
                <Link key={l.to} to={l.to} style={{ marginRight: "1rem" }}>{l.label} →</Link>
              ))}
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>CLI</h2>
        <pre className="code-block mono">{`uap init          # create workspace
uap run           # execute agent
uap prove         # generate proof bundle
uap verify        # verify run integrity
uap audit         # audit trail
uap passport      # agent passport
uap doctor        # environment check
uap push          # export to cloud (optional)`}</pre>
      </section>

      <section className="section">
        <h2>Integration targets</h2>
        <p className="section-desc">NARNA wraps your orchestrator — it does not replace it.</p>
        <ul className="enterprise-list">
          <li>LangGraph</li>
          <li>CrewAI</li>
          <li>OpenAI Agents SDK</li>
          <li>MCP tools</li>
          <li>Custom runtimes</li>
        </ul>
      </section>
    </div>
  );
}
