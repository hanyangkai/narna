import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { claimRecovery } from "../api";

export default function Recover() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") || "";
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(token));
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    claimRecovery(token)
      .then((out) => {
        setApiKey(out.apiKey);
        localStorage.setItem("uap_api_key", out.apiKey);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [token]);

  const onCopy = async () => {
    if (!apiKey) return;
    try {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
    } catch {
      setError("Copy failed");
    }
  };

  if (!token) {
    return (
      <div className="layout-wide signup-page">
        <header className="page-header">
          <h1>Invalid link</h1>
          <p>
            <Link to="/account">Request a new sign-in link</Link>
          </p>
        </header>
      </div>
    );
  }

  return (
    <div className="layout-wide signup-page">
      <header className="page-header">
        <p className="pill-label">Account</p>
        <h1>{loading ? "Signing you in…" : apiKey ? "You're signed in" : "Link expired"}</h1>
      </header>

      {error && <div className="error">{error}</div>}

      {apiKey && (
        <div className="card signup-card">
          <p>Your new API key:</p>
          <pre className="code-block mono signup-key">{apiKey}</pre>
          <div className="land-cta">
            <button type="button" className="btn btn-primary" onClick={onCopy}>
              {copied ? "Copied ✓" : "Copy key"}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => navigate("/checkout")}>
              Upgrade Pro →
            </button>
            <Link to="/billing" className="btn btn-secondary">
              Billing
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
