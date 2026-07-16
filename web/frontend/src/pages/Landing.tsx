import { Link } from "react-router-dom";
import HeroFlow from "../components/HeroFlow";
import {
  ADAPTERS,
  AGENTIC_QUESTIONS,
  AGENTIC_TRAITS,
  AGENTIC_TREND,
  BRAND,
  COMPATIBILITY,
  MARKETPLACE_PACKAGES,
  POSITIONING,
  PRODUCT_FAMILY,
  SPEC,
  TRUST,
} from "../brand";

const problems = [
  "No portable identity across agents and vendors",
  "No shared governance for multi-agent workflows",
  "Policies rewritten per framework (LangGraph, CrewAI, OpenAI…)",
  "Traces without proof of what was allowed",
  "No cross-agent trust or certification",
];

const does = [
  { title: "Identity", desc: "Know which agent is acting." },
  { title: "Policy", desc: "Know what each agent may do." },
  { title: "Evidence", desc: "Know what agents actually did." },
  { title: "Governance", desc: "Enforce rules across agent fleets." },
  { title: "Trust", desc: "Score confidence through evidence." },
  { title: "Certification", desc: "Prove compliance with governance." },
];

const doesNot = [
  "Train models",
  "Build LLMs",
  "Replace LangGraph / CrewAI / AutoGen",
  "Replace OpenTelemetry",
  "Replace MCP",
  "Replace Docker / Kubernetes",
];

const principles = [
  { title: "Universal", desc: "Works with every Agentic AI stack. No vendor lock-in." },
  { title: "Portable", desc: "Write governance once. Run everywhere." },
  { title: "Compatible", desc: "Integrate — never replace — LangGraph, CrewAI, OTel, MCP…" },
  { title: "Verifiable", desc: "Every agentic decision can be verified." },
  { title: "Open", desc: "Open specification. Open SDK. Community driven." },
];

const stackLayers = [
  "Agentic AI — Multi-Agent · Planning · Tool Calling",
  "LangGraph · CrewAI · AutoGen · OpenAI SDK",
  "OpenTelemetry · MCP · OpenShell",
  "★ NARNA — Identity · Governance · Trust · Evidence · Certification",
  "Docker · Kubernetes · Linux · Cloud",
];

const howSteps = [
  { title: "Pick a Governance Package", desc: "Healthcare · Finance · EU AI Act · Banking" },
  { title: "Load into NARNA Runtime", desc: "governance: package: banking-v2" },
  { title: "Attach via adapter", desc: "narna-langgraph · narna-crewai · narna-openai …" },
  { title: "Enforce · Audit · Verify", desc: "Deny by default; human approval when required" },
  { title: "Agent Passport", desc: "Portable trust signal per agent" },
];

const agentChain = [
  "Sales Agent",
  "Finance Agent",
  "Legal Agent",
  "Browser Agent",
  "Email Agent",
  "Database Agent",
];

export default function Landing() {
  return (
    <>
      <section className="hero hero-navy">
        <div className="layout-wide hero-grid">
          <div>
            <p className="pill-label">Agentic AI · {BRAND.tagline}</p>
            <h1>{BRAND.heroTitle}</h1>
            <p className="hero-primary">{BRAND.heroLead}</p>
            <p className="hero-sub">{BRAND.heroSub}</p>
            <div className="uap-loop">
              {SPEC.pillars.map((s) => (
                <span key={s}>{s}</span>
              ))}
            </div>
            <div className="install-block">
              <label>Install NARNA SDK</label>
              <div className="install-cmd">
                <code>{SPEC.install}</code>
                <Link to="/docs/install" className="btn btn-secondary" style={{ flexShrink: 0 }}>
                  Guide →
                </Link>
              </div>
            </div>
            <div className="hero-actions">
              <Link className="btn btn-primary" to="/docs/quickstart">
                Get Started
              </Link>
              <Link
                className="btn btn-secondary"
                to="/specification"
                style={{
                  background: "rgba(255,255,255,0.1)",
                  borderColor: "rgba(255,255,255,0.25)",
                  color: "#fff",
                }}
              >
                Read {SPEC.name}
              </Link>
            </div>
          </div>
          <HeroFlow />
        </div>
      </section>

      <div className="trusted-bar">
        <p>
          {BRAND.primary} · Open {SPEC.name} · Agent Passport · Governance Packages · Self-host first
        </p>
      </div>

      <div className="layout-wide">
        <section className="section">
          <p className="section-label">Trend</p>
          <h2>The industry is moving to Agentic AI</h2>
          <div className="pipeline" style={{ marginTop: "1.25rem" }}>
            {AGENTIC_TREND.map((t, i) => (
              <span key={t.year} style={{ display: "contents" }}>
                <div className="pipeline-step">
                  <strong>{t.year}</strong>
                  <br />
                  {t.label}
                </div>
                {i < AGENTIC_TREND.length - 1 && <span className="pipeline-arrow">↓</span>}
              </span>
            ))}
          </div>
          <p className="section-desc" style={{ marginTop: "1.25rem" }}>
            Agentic AI means {AGENTIC_TRAITS.slice(0, -1).join(", ")}, and{" "}
            {AGENTIC_TRAITS[AGENTIC_TRAITS.length - 1]}.
            That is where governance becomes non-optional.
          </p>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">Problem</p>
            <h2>Agentic AI without governance</h2>
            <p className="section-desc">
              Frameworks orchestrate. Models reason. Nobody owns portable identity, policy, and trust
              across a fleet of agents.
            </p>
          </div>
          <div>
            <div className="arch-stack" style={{ marginBottom: "1rem" }}>
              {agentChain.map((agent, i) => (
                <div key={agent}>
                  <div className="arch-layer">{agent}</div>
                  {i < agentChain.length - 1 && <div className="arch-arrow">↓</div>}
                </div>
              ))}
            </div>
            <ul className="problem-list">
              {AGENTIC_QUESTIONS.map((p) => (
                <li key={p}>
                  <span className="x">?</span>
                  {p}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="section">
          <p className="section-label">Category</p>
          <h2>{BRAND.oneLiner}</h2>
          <p className="section-desc">{BRAND.category}</p>
          <div className="card" style={{ overflowX: "auto", marginTop: "1.25rem" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Owns</th>
                </tr>
              </thead>
              <tbody>
                {POSITIONING.map((row) => (
                  <tr key={row.company}>
                    <td>
                      <strong>{row.company}</strong>
                    </td>
                    <td style={row.company === "NARNA" ? { color: "var(--accent)", fontWeight: 600 } : undefined}>
                      {row.owns}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">The stack</p>
            <h2>Governance for Agentic AI</h2>
            <p className="section-desc">{BRAND.mission}</p>
          </div>
          <div className="arch-stack">
            {stackLayers.map((layer, i) => (
              <div key={layer}>
                <div className={`arch-layer${layer.includes("NARNA") ? " arch-layer-accent" : ""}`}>
                  {layer}
                </div>
                {i < stackLayers.length - 1 && <div className="arch-arrow">↓</div>}
              </div>
            ))}
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">Agent Passport</p>
            <h2>Verified agents — like Docker Official Image</h2>
            <p className="section-desc">
              Every agent ships a portable passport: identity, capabilities, trust score, and verification
              status. Signal trust across OpenAI, LangGraph, CrewAI, and your own runtimes.
            </p>
            <Link to="/registry" className="btn btn-primary">
              Registry &amp; Passport
            </Link>
          </div>
          <pre className="code-block mono">{`id: research-agent
owner: openai
capabilities:
  - browser
  - wallet
  - memory
trust: 0.97
verified: true`}</pre>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">Governance Package Marketplace</p>
            <h2>Compliance in one line</h2>
            <p className="section-desc">
              Pre-built packages for regulated industries. Load once — NARNA enforces across every agent
              and framework.
            </p>
            <Link to="/packages" className="btn btn-primary">
              Browse packages
            </Link>
          </div>
          <div>
            <div className="feature-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
              {MARKETPLACE_PACKAGES.map((pkg) => (
                <div key={pkg} className="card feature-card" style={{ padding: "0.85rem 1rem" }}>
                  <h3 style={{ margin: 0, fontSize: "0.95rem" }}>{pkg}</h3>
                </div>
              ))}
            </div>
            <pre className="code-block mono" style={{ marginTop: "1rem" }}>{`governance:
  package: banking-v2`}</pre>
          </div>
        </section>

        <section className="section">
          <p className="section-label">Adapters</p>
          <h2>Distribute through Agentic AI frameworks</h2>
          <p className="section-desc">
            Do not compete with LangGraph or OpenAI Agents SDK — install an adapter and get Identity,
            Governance, and Trust on the stack you already use.
          </p>
          <div className="feature-grid" style={{ marginTop: "1.5rem" }}>
            {ADAPTERS.map((name) => (
              <div key={name} className="card feature-card" style={{ padding: "1rem 1.25rem" }}>
                <h3 style={{ margin: 0, fontSize: "0.95rem" }} className="mono">
                  {name}
                </h3>
              </div>
            ))}
          </div>
          <div style={{ marginTop: "1.25rem" }}>
            <Link to="/docs/adapters" className="btn btn-secondary">
              Adapter guide →
            </Link>
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">More problems</p>
            <h2>Intelligence without governance</h2>
          </div>
          <ul className="problem-list">
            {problems.map((p) => (
              <li key={p}>
                <span className="x">✕</span>
                {p}
              </li>
            ))}
          </ul>
        </section>

        <section className="section">
          <p className="section-label">Principles</p>
          <h2>Infrastructure principles</h2>
          <div className="feature-grid" style={{ marginTop: "1.5rem" }}>
            {principles.map((p) => (
              <div key={p.title} className="card feature-card">
                <h3>{p.title}</h3>
                <p>{p.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <p className="section-label">Open specification</p>
          <h2>{SPEC.name} — {SPEC.expand}</h2>
          <p className="section-desc">
            The open standard for Agentic AI governance. NARNA Runtime is the reference implementation.
          </p>
          <div className="pipeline">
            {SPEC.pillars.map((s, i) => (
              <span key={s} style={{ display: "contents" }}>
                <div className="pipeline-step">{s}</div>
                {i < SPEC.pillars.length - 1 && <span className="pipeline-arrow">→</span>}
              </span>
            ))}
          </div>
          <div className="pipeline" style={{ marginTop: "1rem" }}>
            {TRUST.steps.map((s, i) => (
              <span key={s} style={{ display: "contents" }}>
                <div className="pipeline-step">
                  {TRUST.name}: {s}
                </div>
                {i < TRUST.steps.length - 1 && <span className="pipeline-arrow">→</span>}
              </span>
            ))}
          </div>
          <div style={{ marginTop: "1.25rem" }}>
            <Link to="/specification" className="btn btn-primary">
              Read the Spec
            </Link>
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">How it works</p>
            <h2>{BRAND.primary}</h2>
          </div>
          <div className="steps">
            {howSteps.map((s, i) => (
              <div key={s.title} className="step-item">
                <span className="step-num">{i + 1}</span>
                <div>
                  <strong>{s.title}</strong>
                  <span>{s.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <p className="section-label">Capabilities</p>
          <h2>What NARNA does</h2>
          <div className="feature-grid" style={{ marginTop: "1.5rem" }}>
            {does.map((f) => (
              <div key={f.title} className="card feature-card">
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">Non-goals</p>
            <h2>What NARNA does not do</h2>
            <p className="section-desc">
              NARNA makes Agentic AI frameworks work together under one governance standard.
            </p>
          </div>
          <ul className="problem-list">
            {doesNot.map((p) => (
              <li key={p}>
                <span className="x">✕</span>
                {p}
              </li>
            ))}
          </ul>
        </section>

        <section className="section">
          <p className="section-label">Compatibility first</p>
          <h2>Integrates with your Agentic AI stack</h2>
          <div className="feature-grid" style={{ marginTop: "1.5rem" }}>
            {COMPATIBILITY.map((name) => (
              <div key={name} className="card feature-card" style={{ padding: "1rem 1.25rem" }}>
                <h3 style={{ margin: 0, fontSize: "1rem" }}>✓ {name}</h3>
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <p className="section-label">Product family</p>
          <h2>Runtime · Passport · Marketplace · Spec</h2>
          <div className="feature-grid" style={{ marginTop: "1.5rem" }}>
            {PRODUCT_FAMILY.map((name) => (
              <div key={name} className="card feature-card">
                <h3>{name}</h3>
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <p className="section-label">Enterprise</p>
          <h2>{BRAND.enterprise}</h2>
          <p className="section-desc">
            Define governance once. Enforce it across Sales, Finance, Legal, Browser, Email, and Database
            agents — on OpenAI, Claude, LangGraph, CrewAI, MCP, and future runtimes.
          </p>
          <Link to="/enterprise" className="btn btn-primary">
            Enterprise
          </Link>
        </section>

        <section className="section">
          <p className="section-label">Pricing</p>
          <h2>Spec &amp; SDK are free. Cloud is optional.</h2>
          <div className="pricing-grid">
            <div className="card">
              <h3>Developer</h3>
              <div className="price">Free</div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{SPEC.name} + OSS SDK + self-host</p>
            </div>
            <div className="card featured">
              <h3>Cloud</h3>
              <div className="price">
                $19<span style={{ fontSize: "1rem" }}>/mo</span>
              </div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Registry, Agent Passport, certification</p>
            </div>
            <div className="card">
              <h3>Enterprise</h3>
              <div className="price" style={{ fontSize: "1.5rem" }}>Contact</div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Fleet governance + compliance packages</p>
            </div>
          </div>
          <Link to="/pricing" className="btn btn-secondary">
            View all plans →
          </Link>
        </section>

        <section className="section">
          <p className="section-label">Vision</p>
          <h2>{BRAND.primary}</h2>
          <p className="section-desc">{BRAND.vision}</p>
          <div className="community-grid" style={{ marginTop: "1rem" }}>
            <a href={BRAND.github} target="_blank" rel="noreferrer">
              GitHub
            </a>
            <a href={BRAND.discord} target="_blank" rel="noreferrer">
              Discord
            </a>
            <Link to="/docs/what-is-narna">What is NARNA?</Link>
            <Link to="/packages">Packages</Link>
          </div>
        </section>
      </div>
    </>
  );
}
