import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PaymentQr from "../components/PaymentQr";
import {
  checkoutCrypto,
  fetchBillingStatus,
  fetchCryptoConfig,
  fetchCryptoNetworks,
  signupAccount,
  type BillingCryptoCheckoutResponse,
  type BillingCryptoConfig,
  type BillingCryptoNetwork,
  type SignupResponse,
} from "../api";

type Step = "signup" | "key" | "pay" | "done";

export default function Signup() {
  const [step, setStep] = useState<Step>("signup");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [signup, setSignup] = useState<SignupResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const [networks, setNetworks] = useState<BillingCryptoNetwork[]>([]);
  const [cryptoConfig, setCryptoConfig] = useState<BillingCryptoConfig | null>(null);
  const [network, setNetwork] = useState("base");
  const [asset, setAsset] = useState<"usdc" | "usdt">("usdc");
  const [checkout, setCheckout] = useState<BillingCryptoCheckoutResponse | null>(null);
  const [plan, setPlan] = useState<string>("free");

  useEffect(() => {
    fetchCryptoNetworks()
      .then((rows) => {
        setNetworks(rows);
        const base = rows.find((n) => n.id === "base");
        if (base) setNetwork("base");
        else if (rows[0]) setNetwork(rows[0].id);
      })
      .catch(() => undefined);
    fetchCryptoConfig().then(setCryptoConfig).catch(() => undefined);
  }, []);

  const onSignup = async () => {
    setError(null);
    setLoading(true);
    try {
      const out = await signupAccount(email.trim(), name.trim() || undefined);
      setSignup(out);
      localStorage.setItem("uap_api_key", out.apiKey);
      setStep("key");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const copyKey = async () => {
    if (!signup?.apiKey) return;
    try {
      await navigator.clipboard.writeText(signup.apiKey);
      setCopied(true);
    } catch {
      setError("Could not copy — select and copy manually");
    }
  };

  const onPayPro = async () => {
    if (!signup?.apiKey) return;
    setError(null);
    setLoading(true);
    try {
      const out = await checkoutCrypto(signup.apiKey, "cloud", asset, network);
      setCheckout(out);
      setStep("pay");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const pollPlan = async () => {
    if (!signup?.apiKey) return;
    try {
      const st = await fetchBillingStatus(signup.apiKey);
      setPlan(st.plan);
      if (st.plan !== "free") setStep("done");
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    if (step !== "pay") return;
    const t = window.setInterval(pollPlan, 5000);
    return () => window.clearInterval(t);
  }, [step, signup?.apiKey]);

  return (
    <div className="layout-wide signup-page">
      <header className="page-header">
        <p className="pill-label">Sign up</p>
        <h1>Create your NARNA Cloud account</h1>
        <p>
          Free account with an API key. Upgrade to Pro with <strong>USDC / USDT</strong> — no Stripe, no
          card.
        </p>
      </header>

      <div className="signup-steps" aria-label="Progress">
        {(["signup", "key", "pay"] as const).map((s, i) => (
          <span
            key={s}
            className={`signup-step-dot${step === s || (step === "done" && s === "pay") ? " active" : ""}${
              ["key", "pay", "done"].indexOf(step) > i ? " done" : ""
            }`}
          >
            {i + 1}
          </span>
        ))}
      </div>

      {error && <div className="error signup-error">{error}</div>}

      {step === "signup" && (
        <div className="card signup-card">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              autoComplete="email"
            />
          </label>
          <label>
            Name <span className="muted">(optional)</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name or team"
            />
          </label>
          <button
            type="button"
            className="btn btn-primary"
            disabled={loading || !email.trim()}
            onClick={onSignup}
          >
            {loading ? "Creating…" : "Create free account"}
          </button>
          <p className="signup-foot">
            Already have a key? <Link to="/account">Sign in</Link>
          </p>
        </div>
      )}

      {step === "key" && signup && (
        <div className="card signup-card">
          <h2>Save your API key</h2>
          <p className="signup-warn">Shown once. We cannot recover it if you lose it.</p>
          <pre className="code-block mono signup-key">{signup.apiKey}</pre>
          <div className="land-cta">
            <button type="button" className="btn btn-primary" onClick={copyKey}>
              {copied ? "Copied ✓" : "Copy key"}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => setStep("pay")}>
              Upgrade Pro ($20/mo)
            </button>
            <Link to="/ask" className="btn btn-secondary">
              Continue free → Ask
            </Link>
          </div>
        </div>
      )}

      {step === "pay" && signup && (
        <div className="card signup-card">
          <h2>Pay with USDC or USDT</h2>
          <p>Pro is $20/month. Send the exact amount — bot confirms on-chain in a few minutes.</p>
          {!checkout && (
            <>
              <div className="console-bar" style={{ marginTop: "1rem" }}>
                <label>
                  Network
                  <select value={network} onChange={(e) => setNetwork(e.target.value)}>
                    {networks.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Asset
                  <select
                    value={asset}
                    onChange={(e) => setAsset(e.target.value as "usdc" | "usdt")}
                  >
                    <option value="usdc">USDC</option>
                    <option value="usdt">USDT</option>
                  </select>
                </label>
              </div>
              <button
                type="button"
                className="btn btn-primary"
                disabled={loading}
                onClick={onPayPro}
              >
                Create payment invoice
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => setStep("done")}>
                Skip — stay on free
              </button>
            </>
          )}
          {checkout && (
            <div className="invoice-card" style={{ marginTop: "1rem" }}>
              <p>
                <strong>Amount:</strong>{" "}
                <span className="mono">
                  {checkout.expectedAmount} {checkout.asset.toUpperCase()}
                </span>
              </p>
              <p className="mono" style={{ wordBreak: "break-all" }}>
                {checkout.recipientWallet}
              </p>
              <PaymentQr payload={checkout.qrPayload} label="Scan in wallet app" />
              <p className="signup-foot">Waiting for confirmation… Plan: {plan}</p>
              <Link to="/billing" className="btn btn-secondary">
                Open billing dashboard
              </Link>
            </div>
          )}
          {cryptoConfig && (
            <p className="signup-foot muted">
              Treasury ({cryptoConfig.cryptoMode}): same wallet on 5 EVM chains.
            </p>
          )}
        </div>
      )}

      {step === "done" && signup && (
        <div className="card signup-card">
          <h2>You&apos;re all set</h2>
          <p>
            Plan: <strong>{plan === "cloud" ? "Pro" : plan}</strong>
            {plan === "cloud" ? " — active for 30 days" : " — free tier"}
          </p>
          <div className="land-cta">
            <Link to="/ask" className="btn btn-primary">
              Open Ask
            </Link>
            <Link to="/billing" className="btn btn-secondary">
              Billing
            </Link>
            <Link to="/console" className="btn btn-secondary">
              Console
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
