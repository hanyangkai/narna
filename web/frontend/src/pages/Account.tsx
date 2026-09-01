import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { fetchAccountMe, requestRecovery } from "../api";

export default function Account() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("uap_api_key") || "");
  const [plan, setPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<"key" | "email">("email");

  const onSignIn = async () => {
    setError(null);
    setLoading(true);
    const key = apiKey.trim();
    if (!key.startsWith("uap_live_")) {
      setError("Paste a valid uap_live_… API key");
      setLoading(false);
      return;
    }
    try {
      localStorage.setItem("uap_api_key", key);
      const me = await fetchAccountMe(key);
      setPlan(me.plan);
      navigate("/billing");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const onEmailRecovery = async () => {
    setError(null);
    setInfo(null);
    setLoading(true);
    try {
      const out = await requestRecovery(email.trim());
      setInfo(out.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Account</p>
        <h1>Sign in</h1>
        <p>
          No password. Use your API key or get a one-time email link. New here?{" "}
          <Link to="/checkout">Get Pro</Link> or <Link to="/signup">Sign up free</Link>.
        </p>
      </header>

      <div className="checkout-tabs">
        <button
          type="button"
          className={`btn ${tab === "email" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setTab("email")}
        >
          Email link
        </button>
        <button
          type="button"
          className={`btn ${tab === "key" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setTab("key")}
        >
          API key
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {info && <div className="card signup-info">{info}</div>}

      {tab === "email" && (
        <div className="card signup-card">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </label>
          <button
            type="button"
            className="btn btn-primary"
            disabled={loading || !email.trim()}
            onClick={onEmailRecovery}
          >
            {loading ? "…" : "Email me a sign-in link"}
          </button>
        </div>
      )}

      {tab === "key" && (
        <div className="card signup-card">
          <label>
            API key
            <input
              type="password"
              className="mono"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="uap_live_…"
            />
          </label>
          {plan && (
            <p>
              Plan: <strong>{plan}</strong>
            </p>
          )}
          <button type="button" className="btn btn-primary" disabled={loading} onClick={onSignIn}>
            {loading ? "…" : "Continue to billing"}
          </button>
        </div>
      )}
    </div>
  );
}
