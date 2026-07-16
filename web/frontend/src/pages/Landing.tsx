import { Link } from "react-router-dom";
import HeroFlow from "../components/HeroFlow";
import { BRAND, PROTOCOL, PRODUCT_FAMILY, TRUST } from "../brand";

const problems = [
  "No portable identity",
  "No constitution / policy",
  "No permission manifest",
  "No evidence package",
  "No cross-vendor trust",
];

const features = [
  { title: "Identity", desc: "Universal AI Identity — every entity." },
  { title: "Constitution", desc: "constitution.yaml governs, not prompts." },
  { title: "Permission", desc: "Android-style policy manifest." },
  { title: "Evidence", desc: "Proof packages — not mere traces." },
  { title: "Passport", desc: "Public trust view enterprises understand." },
  { title: "Certification", desc: "Verified by NARNA — portable trust." },
];

const howSteps = [
  { title: "Write a Constitution", desc: "constitution.yaml — who / may / must" },
  { title: "Attach to any runtime", desc: "LangGraph · CrewAI · MCP · OpenAI …" },
  { title: "Enforce policy", desc: "Deny by default before side effects" },
  { title: "Collect evidence", desc: "Proof packages via VAP" },
  { title: "Issue Passport / Certify", desc: "Portable trust across vendors" },
];

const archLayers = [
  "NARNA Constitution Layer",
  "Identity · Policy · Evidence · Trust",
  "Passport · Certification · Governance",
  "OpenTelemetry · MCP · Agent SDKs",
  "LangGraph · CrewAI · OpenShell · …",
  "Any Model",
];

const brandLetters = [
  { letter: "N", meaning: "Neural", desc: "Any LLM. Any reasoning engine." },
  { letter: "A", meaning: "Autonomous", desc: "Agents. Automation. Decisions." },
  { letter: "R", meaning: "Rules", desc: "Constitution & governance — not another runtime." },
  { letter: "N", meaning: "Native", desc: "Protocol-native contracts. Spec first." },
  { letter: "A", meaning: "Architecture", desc: "Identity · Governance · Trust layer." },
];

export default function Landing() {
  return (
    <>
      <section className="hero hero-navy">
        <div className="layout-wide hero-grid">
          <div>
            <p className="pill-label">{BRAND.name} · {PROTOCOL.name} Protocol v0.1</p>
            <h1>{BRAND.tagline}</h1>
            <div className="uap-loop">
              {PROTOCOL.steps.map((s) => (
                <span key={s}>{s}</span>
              ))}
            </div>
            <p className="hero-sub">
              {BRAND.contrast} Compatibility first — sits above OpenTelemetry, MCP, and any agent SDK.
            </p>
            <div className="install-block">
              <label>Install NARNA SDK</label>
              <div className="install-cmd">
                <code>{PROTOCOL.install}</code>
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
                Read UAP Spec
              </Link>
            </div>
          </div>
          <HeroFlow />
        </div>
      </section>

      <div className="trusted-bar">
        <p>Open source · Open specification · Self-host first</p>
      </div>

      <div className="layout-wide">
        <section className="section">
          <p className="section-label">Brand</p>
          <h2>{BRAND.expand}</h2>
          <p className="section-desc">{BRAND.elevator}</p>
          <div className="feature-grid">
            {brandLetters.map((b) => (
              <div key={b.meaning} className="card feature-card">
                <h3>
                  <span style={{ color: "var(--accent)" }}>{b.letter}</span> — {b.meaning}
                </h3>
                <p>{b.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">Problem</p>
            <h2>Today&apos;s agents have prompts — not a constitution</h2>
            <p className="section-desc">
              Frameworks own execution. Nobody owns portable identity, policy, and trust across vendors.
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

        <section className="section">
          <p className="section-label">UAP Protocol</p>
          <h2>Understand · Act · Prove</h2>
          <p className="section-desc">Every autonomous action should be explainable, verifiable, and trusted.</p>
          <div className="pipeline">
            {PROTOCOL.steps.map((s, i) => (
              <span key={s} style={{ display: "contents" }}>
                <div className="pipeline-step">{s}</div>
                {i < PROTOCOL.steps.length - 1 && <span className="pipeline-arrow">→</span>}
              </span>
            ))}
          </div>
        </section>

        <section className="section">
          <p className="section-label">VAP Engine</p>
          <h2>Verify · Audit · Prove</h2>
          <p className="section-desc">Trust is not assumed. Trust is earned through evidence.</p>
          <div className="pipeline">
            {TRUST.steps.map((s, i) => (
              <span key={s} style={{ display: "contents" }}>
                <div className="pipeline-step">{s}</div>
                {i < TRUST.steps.length - 1 && <span className="pipeline-arrow">→</span>}
              </span>
            ))}
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">Architecture</p>
            <h2>Constitution Layer. Any framework. Any model.</h2>
            <p className="section-desc">
              {BRAND.name} sits above OpenTelemetry, MCP, and agent SDKs — defining who AI is, what it may do, and why it can be trusted.
            </p>
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
              {BRAND.name} is not a model, not an app, and not competing to own the runtime. It is the Constitution Layer for autonomous AI.
            </p>
          </div>
          <div className="arch-stack">
            {archLayers.map((layer, i) => (
              <div key={layer}>
                <div className="arch-layer">{layer}</div>
                {i < archLayers.length - 1 && <div className="arch-arrow">↓</div>}
              </div>
            ))}
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">How it works</p>
            <h2>Five steps to portable trust</h2>
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
          <p className="section-label">Features</p>
          <h2>Built for governance, not demos</h2>
          <div className="feature-grid" style={{ marginTop: "1.5rem" }}>
            {features.map((f) => (
              <div key={f.title} className="card feature-card">
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="section">
          <p className="section-label">Product family</p>
          <h2>Brand · Protocol · Engine</h2>
          <div className="feature-grid" style={{ marginTop: "1.5rem" }}>
            {PRODUCT_FAMILY.map((name) => (
              <div key={name} className="card feature-card">
                <h3>{name}</h3>
                <p>
                  {name.startsWith("UAP")
                    ? "Open specification"
                    : name.startsWith("VAP")
                      ? "Trust engine"
                      : "NARNA product"}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="section two-col">
          <div>
            <p className="section-label">Open Specification</p>
            <h2>UAP — anyone can implement</h2>
            <p className="section-desc">
              Normative YAML specs and JSON Schemas. MIT licensed. No vendor lock-in.
            </p>
            <Link to="/specification" className="btn btn-primary">
              Read UAP Spec v0.1
            </Link>
          </div>
          <div className="card">
            <table className="spec-table">
              <tbody>
                <tr>
                  <td><strong>Brand</strong></td>
                  <td>{BRAND.name}</td>
                </tr>
                <tr>
                  <td><strong>Protocol</strong></td>
                  <td>{PROTOCOL.name}</td>
                </tr>
                <tr>
                  <td><strong>Trust</strong></td>
                  <td>{TRUST.name}</td>
                </tr>
                <tr>
                  <td><strong>License</strong></td>
                  <td>MIT</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="section">
          <p className="section-label">Moat</p>
          <h2>Open standard. Optional cloud.</h2>
          <div className="moat-flow">
            <span className="moat-step">UAP Spec</span>
            <span className="pipeline-arrow">→</span>
            <span className="moat-step">NARNA SDK</span>
            <span className="pipeline-arrow">→</span>
            <span className="moat-step">NARNA Runtime</span>
            <span className="pipeline-arrow">→</span>
            <span className="moat-step">NARNA Cloud</span>
          </div>
          <p className="section-desc" style={{ textAlign: "center", margin: "0 auto" }}>
            Not a closed platform. Self-host with <code>docker compose up</code> or use hosted telemetry when you need it.
          </p>
        </section>

        <section className="section">
          <p className="section-label">Pricing</p>
          <h2>SDK is free. Cloud is optional.</h2>
          <div className="pricing-grid">
            <div className="card">
              <h3>Developer</h3>
              <div className="price">Free</div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>OSS SDK + self-host</p>
            </div>
            <div className="card featured">
              <h3>Cloud</h3>
              <div className="price">
                $19<span style={{ fontSize: "1rem" }}>/mo</span>
              </div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Hosted audit &amp; history</p>
            </div>
            <div className="card">
              <h3>Enterprise</h3>
              <div className="price" style={{ fontSize: "1.5rem" }}>Contact</div>
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>On-premise + compliance</p>
            </div>
          </div>
          <Link to="/pricing" className="btn btn-secondary">
            View all plans →
          </Link>
        </section>

        <section className="section">
          <p className="section-label">Vision</p>
          <h2>Default runtime for trusted agents</h2>
          <p className="section-desc">
            Just as Git became the standard for version control and Kubernetes for containers,
            {BRAND.name} aims to standardize how agents understand, act, verify, and collaborate.
          </p>
          <div className="community-grid" style={{ marginTop: "1rem" }}>
            <a href={BRAND.github} target="_blank" rel="noreferrer">GitHub</a>
            <a href={BRAND.discord} target="_blank" rel="noreferrer">Discord</a>
            <Link to="/docs/examples">Examples</Link>
            <Link to="/docs">Documentation</Link>
          </div>
        </section>
      </div>
    </>
  );
}
