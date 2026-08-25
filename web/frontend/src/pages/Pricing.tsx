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
          <strong>{PRICING.philosophy}</strong>
        </p>
      </header>

      <div className="land-price-row land-price-row-3" style={{ marginBottom: "2rem" }}>
        {PRICING.plans.map((p) => (
          <div key={p.id} className={`land-price${p.featured ? " land-price-featured" : ""}`}>
            <h3>{p.name}</h3>
            <p className="land-price-amt">
              {p.price}
              {p.period ? <span>{p.period}</span> : null}
            </p>
            <p className="land-price-limit">{p.limit}</p>
            <p className="land-price-limit">History: {p.retention}</p>
            <ul className="land-price-features">
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

      <p style={{ color: "var(--muted)" }}>{PRICING.enterpriseNote}</p>

      <section className="section">
        <h2>Same shape as modern infra</h2>
        <p className="section-desc">
          Free engine on your machine. Paid cloud so every agent and console shares Decision Memory and
          ADQA — analogous to open-source memory engines + managed sync clouds.
        </p>
        <div className="two-col">
          <div className="card feature-card">
            <h3>Pay with USDC / USDT</h3>
            <p>Stablecoin checkout on 5 chains — no card. Bot confirms on-chain.</p>
            <Link to="/billing">Billing →</Link>
          </div>
          <div className="card feature-card">
            <h3>Enterprise</h3>
            <p>On-prem Decision Runtime, SSO, industry packages, SLA.</p>
            <Link to="/enterprise">Contact →</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
