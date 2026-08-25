import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  evaluateDecision,
  fetchDecisionPackages,
  healthCheck,
  type DecisionPackageListing,
  type DecisionResult,
} from "../api";

export default function DecisionConsole() {
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [packages, setPackages] = useState<DecisionPackageListing[]>([]);
  const [provider, setProvider] = useState("legal-decision");
  const [action, setAction] = useState("contract.sign");
  const [evidence, setEvidence] = useState("policy.decision,human.review,contract.hash");
  const [customer, setCustomer] = useState("");
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    healthCheck().then(setApiOk);
    fetchDecisionPackages()
      .then((pkgs) => {
        setPackages(pkgs);
        if (pkgs[0]?.provider) setProvider(pkgs[0].provider);
        if (pkgs[0]?.actions?.[0]) setAction(pkgs[0].actions[0]);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  useEffect(() => {
    const pkg = packages.find((p) => p.provider === provider);
    if (pkg?.actions?.[0]) setAction(pkg.actions[0]);
  }, [provider, packages]);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const evidencePresent = evidence
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const out = await evaluateDecision({
        action,
        provider,
        evidencePresent,
        context: customer ? { customer } : undefined,
      });
      setResult(out.result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const decisionClass =
    result?.decision === "allow"
      ? "badge badge-ok"
      : result?.decision === "deny"
        ? "badge badge-fail"
        : "badge badge-wait";

  return (
    <div className="layout-wide">
      <section>
        <header className="page-header" style={{ paddingTop: "1rem" }}>
          <p className="pill-label">ADQA · Decision OS</p>
          <h1>Decision Quality Console</h1>
          <p>
            Score decisions with DQS (10 attributes) + Decision Guardian. API:{" "}
            {apiOk === null ? "…" : apiOk ? "online" : "offline"}
            {" · "}
            <Link to="/console">Sessions</Link>
            {" · "}
            <Link to="/console/guardian">Guardian</Link>
          </p>
        </header>

        <div className="console-bar" style={{ display: "grid", gap: "0.75rem" }}>
          <label>
            Package
            <select value={provider} onChange={(e) => setProvider(e.target.value)}>
              {packages.map((p) => (
                <option key={p.provider} value={p.provider}>
                  {p.name} ({p.industry || "general"})
                </option>
              ))}
            </select>
          </label>
          <label>
            Action
            <select value={action} onChange={(e) => setAction(e.target.value)}>
              {(packages.find((p) => p.provider === provider)?.actions || [action]).map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
          <label>
            Evidence present (comma-separated)
            <input
              className="mono"
              value={evidence}
              onChange={(e) => setEvidence(e.target.value)}
            />
          </label>
          <label>
            Customer context (optional)
            <input value={customer} onChange={(e) => setCustomer(e.target.value)} />
          </label>
          <button type="button" className="btn btn-primary" onClick={run} disabled={loading}>
            {loading ? "Scoring…" : "Score decision (ADQA)"}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {result && (
          <div style={{ marginTop: "1.5rem" }}>
            <p>
              Decision: <span className={decisionClass}>{result.decision}</span>
              {result.adqa?.dqs != null && (
                <>
                  {" "}
                  · DQS: <span className="mono">{result.adqa.dqs}/100</span>
                  {result.adqa.guardian && (
                    <>
                      {" "}
                      · Guardian: <span className="mono">{result.adqa.guardian}</span>
                    </>
                  )}
                </>
              )}
              {result.riskBand && (
                <>
                  {" "}
                  · Risk: <span className="mono">{result.riskScore}</span> ({result.riskBand})
                </>
              )}
            </p>
            {result.adqa?.attributes && (
              <>
                <h3>Decision Quality attributes</h3>
                <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
                  {JSON.stringify(result.adqa.attributes, null, 2)}
                </pre>
              </>
            )}
            {result.adqa?.lessonsUsed ? (
              <>
                <h3>Decision Memory lessons used</h3>
                <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
                  {JSON.stringify(result.adqa.lessonsUsed, null, 2)}
                </pre>
              </>
            ) : null}
            {result.recommendation && <p>{result.recommendation}</p>}
            {result.reasons && result.reasons.length > 0 && (
              <>
                <h3>Reasons</h3>
                <ul>
                  {result.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </>
            )}
            {result.requiredApprovals && result.requiredApprovals.length > 0 && (
              <>
                <h3>Approvals</h3>
                <p className="mono">{result.requiredApprovals.join(", ")}</p>
              </>
            )}
            <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </section>
    </div>
  );
}
