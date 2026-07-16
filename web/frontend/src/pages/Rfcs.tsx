import { Link } from "react-router-dom";

const RFCS = [
  {
    id: "RFC-0001",
    title: "Universal AI Identity",
    status: "Accepted",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0001-agent-identity.md",
  },
  {
    id: "RFC-0003",
    title: "Agent Passport",
    status: "Accepted",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0003-agent-passport.md",
  },
  {
    id: "RFC-0004",
    title: "NARNA Score",
    status: "Accepted",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0004-narna-score.md",
  },
  {
    id: "RFC-0005",
    title: "Manifest narna.yaml",
    status: "Draft",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0005-narna-yaml-manifest.md",
  },
  {
    id: "RFC-0007",
    title: "Governance Package",
    status: "Draft",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0007-governance-package.md",
  },
  {
    id: "RFC-0008",
    title: "Constitution Runtime",
    status: "Draft",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0008-constitution-runtime.md",
  },
  {
    id: "RFC-0009",
    title: "Constitution Compatibility",
    status: "Draft",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0009-constitution-compatibility.md",
  },
  {
    id: "RFC-0010",
    title: "UGS Rename (UAP → UGS)",
    status: "Draft",
    href: "https://github.com/hanyangkai/narna/blob/main/rfcs/RFC-0010-ugs-rename.md",
  },
];

export default function Rfcs() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Community</p>
        <h1>Request for Comments (RFC)</h1>
        <p>
          NARNA evolves through community RFCs — like Kubernetes KEPs or Python PEPs. Spec before code.
          Never Replace. Always Extend.
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <div className="card">
          <h3>Lifecycle</h3>
          <pre className="code-block mono" style={{ margin: 0 }}>
            Draft → Review → Accepted → Implemented → Final
          </pre>
        </div>
      </section>

      <section className="section">
        <h2>Index</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>RFC</th>
              <th>Title</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {RFCS.map((r) => (
              <tr key={r.id}>
                <td className="mono">{r.id}</td>
                <td>
                  <a href={r.href} target="_blank" rel="noreferrer">
                    {r.title}
                  </a>
                </td>
                <td>{r.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: "1.25rem" }}>
          <a href="https://github.com/hanyangkai/narna/tree/main/rfcs" className="btn btn-secondary" target="_blank" rel="noreferrer">
            All RFCs on GitHub →
          </a>
          <Link to="/docs/borrow-the-wave" className="btn btn-primary" style={{ marginLeft: "0.75rem" }}>
            Borrow the Wave
          </Link>
        </div>
      </section>
    </div>
  );
}
