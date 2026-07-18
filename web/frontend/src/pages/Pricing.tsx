import { Link } from "react-router-dom";
import { PRICING } from "../brand";

export default function Pricing() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Pricing</p>
        <h1>{PRICING.tagline}</h1>
        <p>{PRICING.subline}</p>
        <p style={{ color: "var(--muted)", marginTop: "0.75rem" }}>
          <strong>{PRICING.philosophy}</strong> — Logical Agent = identity. Execution Unit = usage.{" "}
          <strong>1 EU = 1 GU</strong> by default; spawn trees cannot cheat agent-count pricing.
        </p>
      </header>

      <div className="pricing-grid">
        {PRICING.plans.map((p) => (
          <div key={p.id} className={`card ${p.featured ? "featured" : ""}`}>
            <h3>{p.name}</h3>
            <div className="price">
              {p.price}
              {p.period && <span style={{ fontSize: "1rem", fontWeight: 400 }}>{p.period}</span>}
            </div>
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{p.limit}</p>
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>History: {p.retention}</p>
            <ul style={{ paddingLeft: "1.1rem", fontSize: "0.9rem", color: "var(--muted)", margin: "1rem 0" }}>
              {p.features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            <Link to={p.ctaTo} className={`btn ${p.featured ? "btn-primary" : "btn-secondary"}`}>
              {p.cta}
            </Link>
          </div>
        ))}
      </div>

      <section className="section">
        <h2>Beyond subscription</h2>
        <div className="two-col">
          <div className="card feature-card">
            <h3>Passport Verification API</h3>
            <p>
              <code>GET /v1/passport/&#123;agentId&#125;</code> — verified identity, trust score, active policy.
              Metered or included in Cloud plans.
            </p>
          </div>
          <div className="card feature-card">
            <h3>Certification</h3>
            <p>NARNA Certified agents and governance packages — from $100 to enterprise tiers.</p>
          </div>
          <div className="card feature-card">
            <h3>Governance Marketplace</h3>
            <p>
              Authors publish HIPAA, EU AI Act, Finance, and custom packages. NARNA takes 20% — the AWS
              Marketplace of governance.
            </p>
            <Link to="/packages">Browse packages →</Link>
          </div>
          <div className="card feature-card">
            <h3>Enterprise</h3>
            <p>SOC2, ISO27001, SSO, RBAC, on-prem, and compliance — typically $20k+/year.</p>
            <Link to="/enterprise">Contact sales →</Link>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Payment</h2>
        <div className="two-col">
          <div className="card feature-card">
            <h3>V1 — Card</h3>
            <p>Stripe Checkout: card, Apple Pay, Google Pay.</p>
          </div>
          <div className="card feature-card">
            <h3>V2 — Stablecoin (optional)</h3>
            <p>USDC/USDT on major chains for teams that prefer on-chain billing.</p>
          </div>
        </div>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginTop: "0.75rem" }}>
          Local runtime never requires payment. Login only when you need Registry, Passport, or Certification.
        </p>
      </section>

      <p style={{ marginTop: "1rem" }}>
        <Link to="/console">Open Console →</Link>
        {" · "}
        <Link to="/docs/quickstart">Self-host guide →</Link>
      </p>
    </div>
  );
}
