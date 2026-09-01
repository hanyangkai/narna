import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { DEFAULT_DEV_KEY, fetchAccountMe } from "../api";

export default function Account() {
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("uap_api_key") || "");
  const [email, setEmail] = useState<string | null>(null);
  const [plan, setPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
      setEmail(me.email);
      setPlan(me.plan);
      navigate("/billing");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const key = localStorage.getItem("uap_api_key");
    if (!key || key === DEFAULT_DEV_KEY) return;
    fetchAccountMe(key)
      .then((me) => {
        setEmail(me.email);
        setPlan(me.plan);
      })
      .catch(() => undefined);
  }, []);

  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Account</p>
        <h1>Sign in with API key</h1>
        <p>
          No password — your <code>uap_live_…</code> key from signup is your credential. Lost it?{" "}
          <Link to="/signup">Create a new account</Link> (one email = one account).
        </p>
      </header>

      <div className="card signup-card">
        {email && (
          <p style={{ marginBottom: "1rem" }}>
            Signed in as <strong>{email}</strong> · plan <strong>{plan}</strong>
          </p>
        )}
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
        {error && <div className="error">{error}</div>}
        <div className="land-cta" style={{ marginTop: "1rem" }}>
          <button type="button" className="btn btn-primary" disabled={loading} onClick={onSignIn}>
            {loading ? "…" : "Continue to billing"}
          </button>
          <Link to="/signup" className="btn btn-secondary">
            Sign up
          </Link>
        </div>
      </div>
    </div>
  );
}
