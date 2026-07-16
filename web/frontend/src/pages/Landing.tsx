import { Link } from "react-router-dom";
import HeroFlow from "../components/HeroFlow";
import {
  BRAND,
  COMPATIBILITY,
  POSITIONING,
  PRODUCT_FAMILY,
  SPEC,
  TRUST,
} from "../brand";

const problems = [
  "No portable identity across vendors",
  "No shared governance standard",
  "Policies rewritten per framework",
  "Traces without proof",
  "No cross-stack trust",
];

const does = [
  { title: "Identity", desc: "Know who AI is." },
  { title: "Policy", desc: "Know what AI may do." },
  { title: "Evidence", desc: "Know what AI actually did." },
  { title: "Governance", desc: "Enforce organizational rules." },
  { title: "Trust", desc: "Measure confidence through evidence." },
  { title: "Certification", desc: "Prove compliance with governance." },
];

const doesNot = [
  "Train models",
  "Build LLMs",
  "Replace agent frameworks",
  "Replace OpenTelemetry",
  "Replace MCP",
  "Replace Docker / Kubernetes",
];

const principles = [
  { title: "Universal", desc: "Works with every AI stack. No vendor lock-in." },
  { title: "Portable", desc: "Write governance once. Run everywhere." },
  { title: "Compatible", desc: "Integrate — never replace — OTel, MCP, OpenAI, Anthropic…" },
  { title: "Verifiable", desc: "Every autonomous decision can be verified." },
  { title: "Open", desc: "Open specification. Open SDK. Community driven." },
];

const stackLayers = [
  "Applications · AI Products",
  "OpenAI · Claude · Gemini · Llama",
  "OpenAI SDK · LangGraph · CrewAI · AutoGen",
  "OpenTelemetry · MCP · OpenShell",
  "★ NARNA Runtime — Identity · Governance · Evidence · Trust",
  "Docker · Kubernetes · Linux · Cloud",
];

const howSteps = [
  { title: "Define a Governance Package", desc: "identity · permissions · policies · trust" },
  { title: "Load into NARNA Runtime", desc: "provider@version or local YAML" },
  { title: "Attach to any host", desc: "OpenAI · Claude · LangGraph · MCP …" },
  { title: "Enforce · Audit · Verify", desc: "Deny by default; evidence required" },
  { title: "Certify & Passport", desc: "Portable trust across vendors" },
];

export default function Landing() {
  return (
    <>
      <section className="hero hero-navy">
        <div className="layout-wide hero-grid">
          <div>
            <img
              src="/brand/narna-logo.png"
              alt="NARNA — Govern Once. Run Anywhere."
              className="hero-brand-mark"
            />
            <p className="pill-label">Infrastructure · {SPEC.name} v0.1</p>
            <h1>{BRAND.tagline}</h1>
            <p className="hero-primary">{BRAND.primary}</p>
            <div className="uap-loop">
              {SPEC.pillars.map((s) => (
                <span key={s}>{s}</span>
              ))}
            </div>
            <p className="hero-sub">
              {BRAND.oneLiner} {BRAND.contrast} Like Docker for containers — NARNA for AI governance.
            </p>
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
        <p>Open source · Open specification ({SPEC.name}) · Self-host first · Infrastructure layer</p>
      </div>

      <div className="layout-wide">
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
            <p className="section-label">Problem</p>
            <h2>Intelligence without governance</h2>
            <p className="section-desc">
              Frameworks execute. Models reason. Nobody owns portable identity, policy, and trust across vendors.
            </p>
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

        <section className="section two-col">
          <div>
            <p className="section-label">The AI stack</p>
            <h2>Governance sits with the infrastructure</h2>
            <p className="section-desc">
              {BRAND.mission}
            </p>
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
            The open standard for AI governance. NARNA Runtime is the reference implementation.
            Anyone can implement UGS — like anyone can implement OCI or OTel.
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
                <div className="pipeline-step">{TRUST.name}: {s}</div>
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
              Instead, NARNA makes them work together under one governance standard.
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
          <h2>Integrates with your stack</h2>
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
          <h2>Runtime · Spec · Cloud</h2>
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
            Define governance once. Enforce it across OpenAI, Claude, Gemini, local LLMs, LangGraph,
            CrewAI, MCP servers, and future runtimes — without rewriting policies for each platform.
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
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Registry, passport, certification</p>
            </div>
            <div className="card">
              <h3>Enterprise</h3>
              <div className="price" style={{ fontSize: "1.5rem" }}>Contact</div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Fleet governance + compliance</p>
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
