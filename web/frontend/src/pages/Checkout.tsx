import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PaymentQr from "../components/PaymentQr";
import {
  checkoutCrypto,
  fetchAuthConfig,
  fetchBillingStatus,
  fetchCryptoNetworks,
  requestRecovery,
  signupAccount,
  type BillingCryptoCheckoutResponse,
  type BillingCryptoNetwork,
} from "../api";

type Phase = "email" | "pay" | "done";

const FALLBACK_NETWORKS: BillingCryptoNetwork[] = [
  { id: "base", name: "Base", chainId: 8453, assets: ["usdc", "usdt"], rpcConfigured: true },
  { id: "ethereum", name: "Ethereum", chainId: 1, assets: ["usdc", "usdt"], rpcConfigured: true },
  { id: "polygon", name: "Polygon", chainId: 137, assets: ["usdc", "usdt"], rpcConfigured: true },
  { id: "arbitrum", name: "Arbitrum One", chainId: 42161, assets: ["usdc", "usdt"], rpcConfigured: true },
  { id: "bsc", name: "BNB Smart Chain", chainId: 56, assets: ["usdc", "usdt"], rpcConfigured: true },
];

function networkLabel(networks: BillingCryptoNetwork[], id: string): string {
  return networks.find((n) => n.id === id)?.name ?? id;
}

export default function Checkout() {
  const [phase, setPhase] = useState<Phase>("email");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("uap_api_key") || "");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkout, setCheckout] = useState<BillingCryptoCheckoutResponse | null>(null);
  const [plan, setPlan] = useState("free");
  const [proUsd, setProUsd] = useState(20);
  const [networks, setNetworks] = useState<BillingCryptoNetwork[]>(FALLBACK_NETWORKS);
  const [network, setNetwork] = useState("base");
  const [asset, setAsset] = useState<"usdc" | "usdt">("usdc");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchAuthConfig()
      .then((c) => setProUsd(c.proUsd))
      .catch(() => undefined);
    fetchCryptoNetworks()
      .then((rows) => {
        if (rows.length > 0) {
          setNetworks(rows);
          if (!rows.some((n) => n.id === network)) {
            setNetwork(rows.find((n) => n.id === "base")?.id ?? rows[0].id);
          }
        }
      })
      .catch(() => undefined);
  }, []);

  const selectedNetwork = networks.find((n) => n.id === network);
  const assetsForNetwork = selectedNetwork?.assets ?? ["usdc", "usdt"];

  useEffect(() => {
    if (!assetsForNetwork.includes(asset)) {
      setAsset(assetsForNetwork[0] as "usdc" | "usdt");
    }
  }, [asset, assetsForNetwork]);

  const payNetworkName = useMemo(() => {
    if (checkout) return networkLabel(networks, checkout.network);
    return selectedNetwork?.name ?? network;
  }, [checkout, networks, network, selectedNetwork?.name]);

  const startPay = async (key: string, net = network, tok = asset) => {
    setApiKey(key);
    localStorage.setItem("uap_api_key", key);
    const out = await checkoutCrypto(key, "cloud", tok, net);
    setCheckout(out);
    setNetwork(out.network);
    setAsset(out.asset as "usdc" | "usdt");
    setPhase("pay");
  };

  const onContinue = async () => {
    setError(null);
    setInfo(null);
    setLoading(true);
    const em = email.trim();
    try {
      const out = await signupAccount(em, name.trim() || undefined);
      setApiKey(out.apiKey);
      localStorage.setItem("uap_api_key", out.apiKey);
      if (out.emailSent) {
        setInfo("We also emailed your API key for safekeeping.");
      }
      await startPay(out.apiKey);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.includes("409") || msg.toLowerCase().includes("already registered")) {
        const rec = await requestRecovery(em);
        setInfo(rec.message);
        if (apiKey.startsWith("uap_live_")) {
          setError(null);
          try {
            await startPay(apiKey);
          } catch (payErr) {
            setError(payErr instanceof Error ? payErr.message : String(payErr));
          }
        } else {
          setError("Check your email for a sign-in link, then return here to pay.");
        }
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const onPayWithExistingKey = async () => {
    setError(null);
    setLoading(true);
    try {
      await startPay(apiKey.trim());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const onSwitchNetwork = async () => {
    if (!apiKey.startsWith("uap_live_")) return;
    setError(null);
    setLoading(true);
    try {
      await startPay(apiKey, network, asset);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (phase !== "pay" || !apiKey) return;
    const poll = async () => {
      try {
        const st = await fetchBillingStatus(apiKey);
        setPlan(st.plan);
        if (st.plan !== "free") setPhase("done");
      } catch {
        /* ignore */
      }
    };
    poll();
    const t = window.setInterval(poll, 4000);
    return () => window.clearInterval(t);
  }, [phase, apiKey]);

  const copyAmount = async () => {
    if (!checkout) return;
    try {
      await navigator.clipboard.writeText(checkout.expectedAmount);
      setCopied(true);
    } catch {
      setError("Copy failed");
    }
  };

  const copyWallet = async () => {
    if (!checkout) return;
    try {
      await navigator.clipboard.writeText(checkout.recipientWallet);
    } catch {
      setError("Copy failed");
    }
  };

  return (
    <div className="layout-wide checkout-page">
      <header className="page-header how-hero">
        <p className="pill-label">Checkout</p>
        <h1>NARNA Pro — ${proUsd}/mo</h1>
        <p className="how-hero-lead">
          Pay with <strong>USDC or USDT</strong> on any supported EVM chain — same treasury wallet on
          Ethereum, Base, Polygon, Arbitrum, BNB Chain. Base recommended (lowest fees).
        </p>
      </header>

      {error && <div className="error signup-error">{error}</div>}
      {info && !error && <div className="card signup-info">{info}</div>}

      {phase === "email" && (
        <div className="card signup-card checkout-card">
          <h2>1. Your email &amp; chain</h2>
          <p className="muted">Creates a free account + API key, then opens payment.</p>
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
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Team name" />
          </label>
          <div className="checkout-chain-row">
            <label>
              Network
              <select value={network} onChange={(e) => setNetwork(e.target.value)}>
                {networks.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.name}
                    {n.id === "base" ? " (recommended)" : ""}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Token
              <select value={asset} onChange={(e) => setAsset(e.target.value as "usdc" | "usdt")}>
                {assetsForNetwork.map((a) => (
                  <option key={a} value={a}>
                    {a.toUpperCase()}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button
            type="button"
            className="btn btn-primary btn-block"
            disabled={loading || !email.trim()}
            onClick={onContinue}
          >
            {loading
              ? "…"
              : `Continue — pay $${proUsd} ${asset.toUpperCase()} on ${selectedNetwork?.name ?? network}`}
          </button>

          <details className="checkout-existing" style={{ marginTop: "1.25rem" }}>
            <summary>Already have an API key?</summary>
            <label style={{ marginTop: "0.75rem" }}>
              API key
              <input
                type="password"
                className="mono"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="uap_live_…"
              />
            </label>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={loading || !apiKey.startsWith("uap_live_")}
              onClick={onPayWithExistingKey}
            >
              Pay with this key
            </button>
            <p className="signup-foot">
              Lost key? <Link to="/account">Email recovery</Link>
            </p>
          </details>
        </div>
      )}

      {phase === "pay" && checkout && (
        <div className="card signup-card checkout-card checkout-pay">
          <h2>2. Send exact amount</h2>
          <p className="checkout-amount">
            <span className="mono">{checkout.expectedAmount}</span>{" "}
            <strong>{checkout.asset.toUpperCase()}</strong> on <strong>{payNetworkName}</strong>
          </p>
          <p className="signup-foot muted">
            Same wallet on all 5 EVM chains — send only on <strong>{payNetworkName}</strong> for this
            invoice.
          </p>
          <div className="land-cta checkout-copy-row">
            <button type="button" className="btn btn-secondary btn-sm" onClick={copyAmount}>
              {copied ? "Copied amount ✓" : "Copy amount"}
            </button>
            <button type="button" className="btn btn-secondary btn-sm" onClick={copyWallet}>
              Copy wallet
            </button>
            {checkout.url.startsWith("http") || checkout.url.startsWith("ethereum:") ? (
              <a className="btn btn-primary btn-sm" href={checkout.url} target="_blank" rel="noreferrer">
                Open wallet
              </a>
            ) : null}
          </div>
          <p className="mono checkout-wallet">{checkout.recipientWallet}</p>
          <PaymentQr payload={checkout.qrPayload} label={`Scan ${checkout.asset.toUpperCase()} on ${payNetworkName}`} />
          <p className="signup-foot">
            Waiting for on-chain confirmation… (usually 1–3 min) · Plan: {plan}
          </p>
          <p className="signup-foot muted">Invoice: {checkout.invoiceId}</p>

          <details className="checkout-existing" style={{ marginTop: "1rem" }}>
            <summary>Pay on a different chain instead?</summary>
            <div className="checkout-chain-row" style={{ marginTop: "0.75rem" }}>
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
                Token
                <select value={asset} onChange={(e) => setAsset(e.target.value as "usdc" | "usdt")}>
                  {assetsForNetwork.map((a) => (
                    <option key={a} value={a}>
                      {a.toUpperCase()}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={loading || (network === checkout.network && asset === checkout.asset)}
              onClick={onSwitchNetwork}
              style={{ marginTop: "0.5rem" }}
            >
              {loading ? "…" : "Create new invoice on this chain"}
            </button>
          </details>
        </div>
      )}

      {phase === "done" && (
        <div className="card signup-card checkout-card checkout-done">
          <h2>Pro active</h2>
          <p>Payment confirmed. Your plan is live for 30 days.</p>
          <div className="land-cta">
            <Link to="/ask" className="btn btn-primary">
              Open Ask
            </Link>
            <Link to="/billing" className="btn btn-secondary">
              Billing
            </Link>
            <Link to="/download" className="btn btn-secondary">
              Desktop free
            </Link>
          </div>
        </div>
      )}

      <p className="signup-foot" style={{ textAlign: "center", marginTop: "2rem" }}>
        Desktop agent is always free · <Link to="/download">Download</Link> ·{" "}
        <Link to="/pricing">Pricing</Link>
      </p>
    </div>
  );
}
