import { Link } from "react-router-dom";

const plans = [
  {
    name: "Developer",
    price: "Free",
    period: "",
    events: "10k events/mo",
    retention: "7 days",
    features: ["OSS SDK", "Self-host", "CLI tools", "Local audit"],
    cta: "Get Started",
    ctaTo: "/docs/install",
    featured: false,
  },
  {
    name: "Cloud Pro",
    price: "$19",
    period: "/mo",
    events: "500k events/mo",
    retention: "90 days",
    features: ["Hosted audit", "Run history", "Proof verification", "Card or USDC/USDT"],
    cta: "Subscribe",
    ctaTo: "/billing",
    featured: true,
  },
  {
    name: "Cloud Team",
    price: "$49",
    period: "/mo",
    events: "2M events/mo",
    retention: "1 year",
    features: ["Everything in Pro", "Team usage", "Priority support"],
    cta: "Subscribe",
    ctaTo: "/billing",
    featured: false,
  },
  {
    name: "Enterprise",
    price: "Contact",
    period: "",
    events: "Custom",
    retention: "Custom",
    features: ["On-premise", "RBAC", "SSO", "SOC2", "Compliance audit"],
    cta: "Contact",
    ctaTo: "/enterprise",
    featured: false,
  },
];

export default function Pricing() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Pricing</p>
        <h1>SDK is free. Cloud is optional.</h1>
        <p>
          Like GitHub: UGS is open. NARNA Cloud is the hosted layer. Pay only for audit, logs, and history when you need it.
        </p>
      </header>

      <div className="pricing-grid">
        {plans.map((p) => (
          <div key={p.name} className={`card ${p.featured ? "featured" : ""}`}>
            <h3>{p.name}</h3>
            <div className="price">
              {p.price}
              {p.period && <span style={{ fontSize: "1rem", fontWeight: 400 }}>{p.period}</span>}
            </div>
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{p.events}</p>
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Retention: {p.retention}</p>
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
        <h2>Payment methods</h2>
        <div className="two-col">
          <div className="card feature-card">
            <h3>Card</h3>
            <p>Stripe Checkout. Set up with <code>UAP_BILLING_MODE=stripe</code>.</p>
          </div>
          <div className="card feature-card">
            <h3>Stablecoin</h3>
            <p>USDC/USDT on Ethereum, Polygon, Base, Arbitrum, BSC. On-chain bot confirms payment.</p>
          </div>
        </div>
      </section>

      <p style={{ marginTop: "1rem" }}>
        <Link to="/console">Open Console →</Link>
        {" · "}
        <Link to="/docs/quickstart">Self-host guide →</Link>
      </p>
    </div>
  );
}
