import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "";

type PassportView = {
  agentId: string;
  name: string;
  version: string;
  creator: string;
  category: string;
  capabilities: string[];
  trustScore: number | null;
  stars: number;
  downloads: number;
  executions: number;
  publishedAt: string;
  verified: boolean;
  badge?: string | null;
  level?: string | null;
  levelLabel?: string | null;
  certification?: Record<string, unknown> | null;
  passport: Record<string, unknown> | null;
};

function constitutionFromPassport(passport: Record<string, unknown> | null) {
  if (!passport) return null;
  const c = passport.constitution;
  if (!c || typeof c !== "object") return null;
  return c as { constitutionId?: string; constitutionHash?: string; version?: string };
}

export default function PassportPage() {
  const { agentId } = useParams();
  const [data, setData] = useState<PassportView | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;
    fetch(`${API_BASE}/v1/passport/${agentId}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [agentId]);

  const star = async () => {
    if (!agentId) return;
    await fetch(`${API_BASE}/v1/registry/agents/${agentId}/star`, { method: "POST" });
    const res = await fetch(`${API_BASE}/v1/passport/${agentId}`);
    if (res.ok) setData(await res.json());
  };

  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Passport</p>
        <h1>{data?.name || agentId}</h1>
        <p>Public identity, constitution citation, and trust — portable across vendors.</p>
      </header>

      {error && <div className="error">{error}</div>}

      {data && (
        <div className="two-col">
          <div className="card">
            <p>
              <strong>Agent ID:</strong> <span className="mono">{data.agentId}</span>
            </p>
            <p>
              <strong>Version:</strong> {data.version}
            </p>
            <p>
              <strong>Creator:</strong> {data.creator}
            </p>
            <p>
              <strong>Category:</strong> {data.category}
            </p>
            <p>
              <strong>Capabilities:</strong> {data.capabilities.join(", ") || "—"}
            </p>
            {(() => {
              const c = constitutionFromPassport(data.passport);
              if (!c) return null;
              return (
                <p>
                  <strong>Constitution:</strong>{" "}
                  <span className="mono">{c.constitutionId || "—"}</span>
                  {c.version && (
                    <span style={{ color: "var(--muted)" }}> · v{c.version}</span>
                  )}
                </p>
              );
            })()}
            <p>
              <strong>Trust score:</strong>{" "}
              {data.trustScore != null ? data.trustScore.toFixed(3) : "—"}
              {data.verified && (
                <span className="badge badge-ok" style={{ marginLeft: "0.5rem" }}>
                  {data.badge || "NARNA Certified"}
                  {data.levelLabel ? ` · ${data.levelLabel}` : data.level ? ` · ${data.level}` : ""}
                </span>
              )}
            </p>
            {data.certification && (
              <p>
                <strong>Certification:</strong>{" "}
                <span className="mono">
                  {String((data.certification as { certificationId?: string }).certificationId || "—")}
                </span>
              </p>
            )}
            <p>
              <strong>Stars:</strong> {data.stars} · <strong>Downloads:</strong> {data.downloads} ·{" "}
              <strong>Executions:</strong> {data.executions}
            </p>
            <p>
              <strong>Published:</strong>{" "}
              <span className="mono">{data.publishedAt || "—"}</span>
            </p>
            <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
              <button type="button" className="btn btn-primary" onClick={star}>
                ★ Star
              </button>
              <Link to="/registry" className="btn btn-secondary">
                ← Registry
              </Link>
            </div>
          </div>
          <div className="card">
            <h3>Passport JSON</h3>
            <pre className="code-block mono" style={{ maxHeight: 420, overflow: "auto" }}>
              {JSON.stringify(data.passport || data, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
