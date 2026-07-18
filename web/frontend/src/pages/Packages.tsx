import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import PaddleCheckout from "../components/PaddleCheckout";
import { DEFAULT_DEV_KEY, purchasePackage, verifyPackageSession } from "../api";

const API_BASE = import.meta.env.VITE_API_URL || "";

type PackageRow = {
  packageId: string;
  name: string;
  version: string;
  provider: string;
  packageKind: string;
  license: string;
  disclaimer: string;
  packageHash: string;
  priceUsd?: number;
  takeRateBps?: number;
  stars: number;
  downloads: number;
  publishedAt: string;
};

export default function Packages() {
  const [packages, setPackages] = useState<PackageRow[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiKey] = useState(() => localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY);
  const [searchParams] = useSearchParams();

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      const res = await fetch(`${API_BASE}/v1/packages?${params}`);
      if (!res.ok) throw new Error(await res.text());
      setPackages(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPackages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    // Paddle returns ?_ptxn=txn_… ; Stripe returns ?session_id=cs_…
    const sessionId =
      searchParams.get("session_id") ||
      searchParams.get("_ptxn") ||
      searchParams.get("txn");
    if (searchParams.get("paid") === "1" && sessionId) {
      verifyPackageSession(apiKey, sessionId)
        .then((out) => {
          setMsg(`${out.message} · status: ${out.status} · mode: ${out.mode}`);
          load();
        })
        .catch((e) => setError(e instanceof Error ? e.message : String(e)));
    } else if (searchParams.get("paid") === "1") {
      setMsg("Payment return — if pack not unlocked, wait for Paddle webhook or open with ?_ptxn=");
    } else if (searchParams.get("canceled") === "1") {
      setError("Checkout canceled — no charge.");
    }
  }, [searchParams, apiKey]);

  async function onBuy(packageId: string) {
    setMsg(null);
    setError(null);
    try {
      const out = await purchasePackage(apiKey, packageId);
      if (out.checkoutUrl) {
        setMsg("Redirecting to Paddle Checkout…");
        window.location.href = out.checkoutUrl;
        return;
      }
      setMsg(`${out.message} · status: ${out.status} · mode: ${out.mode} · GU: ${out.guCharged}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="layout-wide">
      <PaddleCheckout />
      <header className="page-header">
        <p className="pill-label">Constitution Marketplace</p>
        <h1>Governance Packages</h1>
        <p>
          Authors publish compliance packs. NARNA takes <strong>20%</strong> — the AWS Marketplace of governance.
        </p>
      </header>

      <div className="card" style={{ marginBottom: "1rem", borderLeft: "3px solid var(--accent, #2563eb)" }}>
        <strong>Global legal mappings (machine-enforceable).</strong> Packages cite real instruments
        (EU AI Act, GDPR, HIPAA, PCI DSS, CCPA/CPRA, UK DPA, PIPL, LGPD, NIST AI RMF, ISO 42001, SOC 2).
        They are <em>not</em> official government publications and <em>not</em> legal advice — pair with counsel
        for production conformity.
      </div>

      <div className="console-bar">
        <label>
          Search
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="provider or id" />
        </label>
        <button type="button" className="btn btn-primary" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Search"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {msg && <div className="card" style={{ marginBottom: "1rem" }}>{msg}</div>}

      <section className="section" style={{ paddingTop: "1rem", borderTop: "none" }}>
        <h2>Published packages</h2>
        {packages.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>
            No packages yet. Seed: <code>narna package publish ./specs/examples/packages/eu-ai-act.yaml</code>
          </p>
        ) : (
          <div className="card" style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Package</th>
                  <th>Provider</th>
                  <th>Kind</th>
                  <th>Price</th>
                  <th>Take</th>
                  <th>Stars</th>
                  <th>Installs</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {packages.map((p) => (
                  <tr key={p.packageId}>
                    <td>
                      <Link to={`/packages/${p.packageId}`}>
                        <strong>{p.name}</strong>
                      </Link>
                      <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{p.packageId}</div>
                    </td>
                    <td>{p.provider}</td>
                    <td>{p.packageKind}</td>
                    <td>{(p.priceUsd ?? 0) === 0 ? "Free" : `$${((p.priceUsd ?? 0) / 100).toFixed(2)}`}</td>
                    <td>{((p.takeRateBps ?? 2000) / 100).toFixed(0)}%</td>
                    <td>{p.stars ?? 0}</td>
                    <td>{p.downloads ?? 0}</td>
                    <td>
                      <button type="button" className="btn btn-secondary" onClick={() => onBuy(p.packageId)}>
                        Buy / Activate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section">
        <h2>CLI</h2>
        <pre className="code-block">{`narna package search
narna package publish ./specs/examples/packages/eu-ai-act.yaml
narna package buy eu-ai-act
narna package pull eu-ai-act --version 1.0.0`}</pre>
      </section>
    </div>
  );
}
