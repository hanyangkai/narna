import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  certifyIsolationPartner,
  evaluateCapability,
  evaluateConstitution,
  fetchGuardianStatus,
  fetchIsolationPartners,
  fetchJurisdictions,
  fetchPartnerCerts,
  healthCheck,
} from "../api";

export default function GuardianConsole() {
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [jurisdictions, setJurisdictions] = useState<unknown[] | null>(null);
  const [partners, setPartners] = useState<unknown[] | null>(null);
  const [certs, setCerts] = useState<unknown[] | null>(null);
  const [capability, setCapability] = useState("create.agent");
  const [constAction, setConstAction] = useState("harm.human");
  const [capResult, setCapResult] = useState<Record<string, unknown> | null>(null);
  const [constResult, setConstResult] = useState<Record<string, unknown> | null>(null);
  const [certResult, setCertResult] = useState<Record<string, unknown> | null>(null);
  const [certPartner, setCertPartner] = useState("docker");
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      const [st, j, p, c] = await Promise.all([
        fetchGuardianStatus(),
        fetchJurisdictions(),
        fetchIsolationPartners(),
        fetchPartnerCerts(),
      ]);
      setStatus(st);
      setJurisdictions((j.jurisdictions as unknown[]) || []);
      setPartners((p.partners as unknown[]) || []);
      setCerts((c.certificates as unknown[]) || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    healthCheck().then(setApiOk);
    refresh();
  }, []);

  async function runCapability() {
    setError(null);
    try {
      setCapResult(await evaluateCapability(capability));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function runConstitution() {
    setError(null);
    try {
      setConstResult(await evaluateConstitution(constAction));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function runCertify() {
    setError(null);
    try {
      setCertResult(await certifyIsolationPartner(certPartner));
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="layout-wide">
      <section>
        <header className="page-header" style={{ paddingTop: "1rem" }}>
          <p className="pill-label">Guardian</p>
          <h1>Guardian Console</h1>
          <p>
            Capability · Constitution · CTI · Jurisdiction · Isolation. API:{" "}
            {apiOk === null ? "…" : apiOk ? "online" : "offline"}
            {" · "}
            <Link to="/console/decision">Decision</Link>
            {" · "}
            <Link to="/console">Sessions</Link>
          </p>
        </header>

        <div className="console-bar">
          <button type="button" className="btn btn-secondary" onClick={refresh}>
            Refresh status
          </button>
        </div>
        {error && <div className="error">{error}</div>}

        {status && (
          <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
            {JSON.stringify(
              {
                ctiHub: status.ctiHub,
                ctiMesh: status.ctiMesh,
                bindings: status.bindings,
                jurisdictions: status.jurisdictions,
                isolation: status.isolation,
                partnerCerts: status.partnerCerts,
                collective: status.collective,
                constitution: status.constitution,
                council: status.council,
              },
              null,
              2
            )}
          </pre>
        )}

        <h2 style={{ marginTop: "2rem" }}>Jurisdictions</h2>
        {jurisdictions && (
          <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
            {JSON.stringify(jurisdictions, null, 2)}
          </pre>
        )}

        <h2 style={{ marginTop: "2rem" }}>Isolation partners</h2>
        {partners && (
          <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
            {JSON.stringify(partners, null, 2)}
          </pre>
        )}

        <h2 style={{ marginTop: "2rem" }}>Partner certify</h2>
        <div className="console-bar">
          <label>
            Partner
            <select value={certPartner} onChange={(e) => setCertPartner(e.target.value)}>
              <option value="docker">docker</option>
              <option value="kubernetes">kubernetes</option>
            </select>
          </label>
          <button type="button" className="btn btn-primary" onClick={runCertify}>
            Certify
          </button>
        </div>
        {certResult && (
          <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
            {JSON.stringify(certResult, null, 2)}
          </pre>
        )}
        {certs && certs.length > 0 && (
          <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
            {JSON.stringify(certs, null, 2)}
          </pre>
        )}

        <h2 style={{ marginTop: "2rem" }}>Capability evaluate</h2>
        <div className="console-bar">
          <label>
            Capability
            <input
              className="mono"
              value={capability}
              onChange={(e) => setCapability(e.target.value)}
            />
          </label>
          <button type="button" className="btn btn-primary" onClick={runCapability}>
            Evaluate
          </button>
        </div>
        {capResult && (
          <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
            {JSON.stringify(capResult, null, 2)}
          </pre>
        )}

        <h2 style={{ marginTop: "2rem" }}>Constitution evaluate</h2>
        <div className="console-bar">
          <label>
            Action
            <input
              className="mono"
              value={constAction}
              onChange={(e) => setConstAction(e.target.value)}
            />
          </label>
          <button type="button" className="btn btn-primary" onClick={runConstitution}>
            Evaluate
          </button>
        </div>
        {constResult && (
          <pre className="mono" style={{ overflow: "auto", fontSize: "0.8rem" }}>
            {JSON.stringify(constResult, null, 2)}
          </pre>
        )}
      </section>
    </div>
  );
}
