import { Link } from "react-router-dom";
import { BRAND } from "../brand";

const BADGES = [
  {
    id: "uap-compatible",
    title: "UGS Compatible",
    desc: "Ships valid Manifest/Constitution + Identity (UGS).",
    src: "/badges/uap-compatible.svg",
  },
  {
    id: "constitution-compatible",
    title: "Constitution Compatible",
    desc: "Governance Package loadable + supports: multi-constitution.",
    src: "/badges/constitution-compatible.svg",
  },
  {
    id: "narna-certified",
    title: "Verified by NARNA",
    desc: "Certification ≥ L1.",
    src: "/badges/narna-certified.svg",
  },
  {
    id: "narna-certified-plus",
    title: "NARNA Certified+",
    desc: "Certification ≥ L2 (VAP proof + trust).",
    src: "/badges/narna-certified-plus.svg",
  },
  {
    id: "enterprise-ready",
    title: "Enterprise Ready",
    desc: "Certification L3 — governance + retention + human review.",
    src: "/badges/enterprise-ready.svg",
  },
];

export default function Compatibility() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Compatibility Program</p>
        <h1>Works with your stack. Earn the badge.</h1>
        <p>
          Like “Works with Kubernetes” — signal that an agent ships portable identity, policy, and trust.
          Never Replace. Always Extend.
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <div className="feature-grid">
          {BADGES.map((b) => (
            <div key={b.id} className="card feature-card">
              <img src={b.src} alt={b.title} height={28} style={{ marginBottom: "0.75rem" }} />
              <h3>{b.title}</h3>
              <p>{b.desc}</p>
              <pre className="code-block mono" style={{ fontSize: "0.75rem" }}>
                {`<img src="/badges/${b.id}.svg" alt="${b.title}" />`}
              </pre>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>How to earn</h2>
        <pre className="code-block mono">{`# 1. Ship metadata
narna manifest --compile

# 2. Prove + certify
narna run --vap --input "hello"
narna certify --vap --level L2 --local

# 3. Publish passport
narna publish --vap`}</pre>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginTop: "1rem" }}>
          <Link to="/docs/certification" className="btn btn-primary">
            Certification guide
          </Link>
          <Link to="/docs/borrow-the-wave" className="btn btn-secondary">
            Borrow the Wave
          </Link>
        </div>
      </section>
    </div>
  );
}
