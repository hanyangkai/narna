import { Link } from "react-router-dom";

const GH = "https://github.com/hanyangkai/narna/blob/main/rfcs/ngs";

const NGS_CORE = [
  { id: "NGS-0001", file: "NGS-0001-ai-identity.md", title: "AI Identity", status: "Accepted" },
  { id: "NGS-0002", file: "NGS-0002-capability.md", title: "Capability Specification", status: "Accepted" },
  { id: "NGS-0003", file: "NGS-0003-permission.md", title: "Permission Model", status: "Accepted" },
  { id: "NGS-0004", file: "NGS-0004-policy.md", title: "Policy Specification", status: "Accepted" },
  { id: "NGS-0005", file: "NGS-0005-evidence.md", title: "Evidence Format", status: "Accepted" },
  { id: "NGS-0006", file: "NGS-0006-trust-score.md", title: "Trust Score Model", status: "Accepted" },
];

const NGS_DERIVED = [
  { id: "NGS-0007", file: "NGS-0007-passport.md", title: "AI Passport", status: "Accepted" },
  { id: "NGS-0008", file: "NGS-0008-governance-package.md", title: "Governance Package", status: "Accepted" },
  { id: "NGS-0009", file: "NGS-0009-certification.md", title: "Certification", status: "Accepted" },
  { id: "NGS-0010", file: "NGS-0010-audit-report.md", title: "Audit Report", status: "Accepted" },
  { id: "NGS-0011", file: "NGS-0011-manifest.md", title: "Governance Manifest", status: "Draft" },
  { id: "NGS-0012", file: "NGS-0012-registry.md", title: "Governance Registry", status: "Accepted" },
  { id: "NGS-0013", file: "NGS-0013-governance-api.md", title: "Governance API", status: "Accepted" },
];

function Table({ rows }: { rows: typeof NGS_CORE }) {
  return (
    <div className="card" style={{ overflowX: "auto" }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td className="mono">
                <a href={`${GH}/${r.file}`} target="_blank" rel="noreferrer">
                  {r.id}
                </a>
              </td>
              <td>{r.title}</td>
              <td>
                <span className={r.status === "Draft" ? "badge badge-wait" : "badge badge-ok"}>{r.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Rfcs() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Standards</p>
        <h1>NGS — NARNA Governance Standards</h1>
        <p>
          IETF-style RFCs for AI Governance. Core six first. Derived standards build on top.{" "}
          <a href={`${GH}/README.md`} target="_blank" rel="noreferrer">
            Full index →
          </a>
        </p>
      </header>

      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <h2>Core six</h2>
        <Table rows={NGS_CORE} />
      </section>

      <section className="section">
        <h2>Derived (Passport → API)</h2>
        <Table rows={NGS_DERIVED} />
      </section>

      <section className="section">
        <h2>Also</h2>
        <p style={{ color: "var(--muted)" }}>
          Legacy <code>RFC-000x</code> files remain for history. OpenAPI:{" "}
          <a
            href="https://github.com/hanyangkai/narna/blob/main/specs/governance-api/openapi.yaml"
            target="_blank"
            rel="noreferrer"
          >
            governance-api/openapi.yaml
          </a>
        </p>
        <p style={{ marginTop: "1rem" }}>
          <Link to="/specification">Specification →</Link>
          {" · "}
          <Link to="/docs">Docs →</Link>
        </p>
      </section>
    </div>
  );
}
