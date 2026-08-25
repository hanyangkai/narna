import { Link } from "react-router-dom";
import { ADAPTERS, BRAND, COMPATIBILITY } from "../brand";

const BADGES = [
  {
    id: "ugs-compatible",
    title: "UGS Compatible",
    desc: "Ships valid Manifest/Constitution + Identity (UGS).",
    src: "/badges/ugs-compatible.svg",
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
        <p className="pill-label">Integrations</p>
        <h1>Works with your stack. Earn the badge.</h1>
        <p>
          {BRAND.name} extends hot AI runtimes — never replaces them. CMEM remembers; NARNA scores
          decisions (ADQA).
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <h2>Hot stacks</h2>
        <p className="section-desc">
          Memory partner:{" "}
          <a href="https://cmem.ai/" target="_blank" rel="noreferrer">
            CMEM / claude-mem
          </a>
          . Orchestrators & models below ship with thin adapters (`narna wrap`).
        </p>
        <div className="feature-grid">
          {COMPATIBILITY.map((name) => (
            <div key={name} className="card feature-card">
              <h3>{name}</h3>
              <p>
                {name === "CMEM"
                  ? "Continuity memory feedstock → ADQA memory attribute + lessons."
                  : `Extend via adapter · ADQA optional (NARNA_ADQA=1).`}
              </p>
            </div>
          ))}
        </div>
        <pre className="code-block mono" style={{ marginTop: "1rem", fontSize: "0.8rem" }}>
          {ADAPTERS.join(" · ")}
        </pre>
        <p style={{ marginTop: "0.75rem" }}>
          <Link to="/docs/integrations">Integration guide →</Link>
          {" · "}
          <a href="https://api.narna.org/v1/integrations" target="_blank" rel="noreferrer">
            GET /v1/integrations
          </a>
        </p>
      </section>

      <section className="section">
        <h2>Compatibility badges</h2>
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
          <Link to="/docs/cmem-bridge" className="btn btn-secondary">
            CMEM bridge
          </Link>
        </div>
      </section>
    </div>
  );
}
