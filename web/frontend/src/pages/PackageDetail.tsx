import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { DEFAULT_DEV_KEY, fetchPackage, purchasePackage, type PackageDetail } from "../api";

type Rule = {
  id?: string;
  effect?: string;
  action?: string;
  description?: string;
  when?: string;
};

function effectClass(effect: string): string {
  const e = effect.toLowerCase();
  if (e === "deny") return "badge badge-fail";
  if (e === "require" || e === "ask") return "badge badge-wait";
  if (e === "allow") return "badge badge-ok";
  return "badge";
}

export default function PackageDetailPage() {
  const { packageId } = useParams();
  const [apiKey] = useState(() => localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY);
  const [pkg, setPkg] = useState<PackageDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    if (!packageId) return;
    fetchPackage(packageId)
      .then(setPkg)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [packageId]);

  async function onBuy() {
    if (!pkg) return;
    setBuying(true);
    setMsg(null);
    setError(null);
    try {
      const out = await purchasePackage(apiKey, pkg.packageId);
      if (out.checkoutUrl) {
        setMsg("Redirecting to Stripe Checkout…");
        window.location.href = out.checkoutUrl;
        return;
      }
      setMsg(`${out.message} · status: ${out.status} · mode: ${out.mode} · GU: ${out.guCharged}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBuying(false);
    }
  }

  if (error) {
    return (
      <div className="layout-wide">
        <p>
          <Link to="/packages">← Marketplace</Link>
        </p>
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!pkg) {
    return (
      <div className="layout-wide">
        <p style={{ color: "var(--muted)" }}>Loading package…</p>
      </div>
    );
  }

  const spec = (pkg.spec || {}) as Record<string, unknown>;
  const principles = (spec.principles as string[]) || [];
  const rules = (spec.rules as Rule[]) || [];
  const supports = (spec.supports as string[]) || [];
  const riskLevel = (spec.riskLevel as string) || "";
  const humanReview = (spec.humanReview as { requiredFor?: string[] }) || {};
  const evidence = (spec.evidence as { mustProve?: string[]; mustLog?: string[]; retentionDays?: number }) || {};
  const legalBasis = (spec.legalBasis as {
    title?: string;
    citation?: string;
    jurisdiction?: string;
    officialUrl?: string;
  }) || null;
  const price = pkg.priceUsd ?? 0;

  return (
    <div className="layout-wide">
      <p>
        <Link to="/packages">← Marketplace</Link>
      </p>

      <header className="page-header" style={{ paddingTop: "0.5rem" }}>
        <p className="pill-label">Governance Package</p>
        <h1>{pkg.name}</h1>
        <p>
          <span className="mono">{pkg.packageId}</span> · v{pkg.version} · by{" "}
          <strong>{pkg.provider}</strong> · {pkg.packageKind}
          {riskLevel ? (
            <>
              {" "}
              · <span className="badge">risk: {riskLevel}</span>
            </>
          ) : null}
        </p>
        {pkg.disclaimer ? (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>⚠️ {pkg.disclaimer}</p>
        ) : null}
      </header>

      <div className="card" style={{ marginBottom: "1rem", display: "flex", flexWrap: "wrap", gap: "2rem", alignItems: "center" }}>
        <div>
          <div className="pill-label">Price</div>
          <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>
            {price === 0 ? "Free" : `$${(price / 100).toFixed(2)}`}
          </div>
        </div>
        <div>
          <div className="pill-label">NARNA take</div>
          <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>{((pkg.takeRateBps ?? 2000) / 100).toFixed(0)}%</div>
        </div>
        <div>
          <div className="pill-label">Stars</div>
          <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>{pkg.stars}</div>
        </div>
        <div>
          <div className="pill-label">Installs</div>
          <div style={{ fontSize: "1.6rem", fontWeight: 700 }}>{pkg.downloads}</div>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <button type="button" className="btn btn-primary" onClick={onBuy} disabled={buying}>
            {buying ? "Processing…" : price === 0 ? "Activate" : "Buy / Activate"}
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {msg && <div className="card" style={{ marginBottom: "1rem" }}>{msg}</div>}

      {legalBasis && (legalBasis.title || legalBasis.citation) && (
        <section className="section" style={{ borderTop: "none", paddingTop: "0.5rem" }}>
          <h2>Legal basis</h2>
          <p>
            <strong>{legalBasis.title}</strong>
            {legalBasis.citation ? <> — {legalBasis.citation}</> : null}
          </p>
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            Jurisdiction: {legalBasis.jurisdiction || "—"}
            {legalBasis.officialUrl ? (
              <>
                {" "}
                ·{" "}
                <a href={legalBasis.officialUrl} target="_blank" rel="noreferrer">
                  Official source
                </a>
              </>
            ) : null}
          </p>
        </section>
      )}

      {principles.length > 0 && (
        <section className="section" style={{ borderTop: legalBasis ? undefined : "none", paddingTop: "0.5rem" }}>
          <h2>Principles</h2>
          <ul>
            {principles.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </section>
      )}

      {rules.length > 0 && (
        <section className="section">
          <h2>Rules</h2>
          <div className="card" style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Effect</th>
                  <th>Action</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r, i) => (
                  <tr key={r.id || i}>
                    <td>
                      <span className={effectClass(r.effect || "")}>{r.effect || "-"}</span>
                    </td>
                    <td className="mono">{r.action || "-"}</td>
                    <td>
                      {r.description || ""}
                      {r.when ? <span style={{ color: "var(--muted)" }}> · when {r.when}</span> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {(humanReview.requiredFor?.length || evidence.mustProve?.length || evidence.mustLog?.length) && (
        <section className="section">
          <h2>Enforcement</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "2rem" }}>
            {humanReview.requiredFor?.length ? (
              <div>
                <h3>Human review required</h3>
                <ul>
                  {humanReview.requiredFor.map((a) => (
                    <li key={a} className="mono">
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {evidence.mustProve?.length ? (
              <div>
                <h3>Must prove</h3>
                <ul>
                  {evidence.mustProve.map((a) => (
                    <li key={a} className="mono">
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {evidence.mustLog?.length ? (
              <div>
                <h3>Must log</h3>
                <ul>
                  {evidence.mustLog.map((a) => (
                    <li key={a} className="mono">
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
          {evidence.retentionDays ? (
            <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
              Evidence retention: {evidence.retentionDays} days
            </p>
          ) : null}
        </section>
      )}

      <section className="section">
        <h2>Load into NARNA Runtime</h2>
        {supports.length > 0 && (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>Supports: {supports.join(", ")}</p>
        )}
        <pre className="code-block">{`governance:
  package: ${pkg.provider}@${pkg.version}

# or via CLI
narna package buy ${pkg.provider}
narna package pull ${pkg.provider} --version ${pkg.version}`}</pre>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
          Package hash: <span className="mono">{pkg.packageHash.slice(0, 24)}…</span>
        </p>
      </section>
    </div>
  );
}
