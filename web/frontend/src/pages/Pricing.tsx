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
            <h3>
              {p.name}
              {"comingSoon" in p && p.comingSoon ? (
                <span style={{ marginLeft: "0.5rem", fontSize: "0.75rem", color: "var(--muted)" }}>
                  · soon
                </span>
              ) : null}
            </h3>
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
        <h2>Free covers the agent</h2>
        <ul className="land-price-features" style={{ maxWidth: "42rem" }}>
          {PRICING.whyUpgrade.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </section>

      <section className="section">
        <h2>Get started</h2>
        <div className="two-col">
          <div className="card feature-card">
            <h3>Desktop (recommended)</h3>
            <p>macOS + Windows portable zips — full agent, no NARNA fee, BYOK.</p>
            <Link to="/download">Download →</Link>
          </div>
          <div className="card feature-card">
            <h3>Ask in browser</h3>
            <p>Paste your LLM key. Or use mock mode. Pro billing is not required.</p>
            <Link to="/ask">Open Ask →</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
