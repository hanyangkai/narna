import { useEffect, useState, type CSSProperties } from "react";
import PaymentQr from "../components/PaymentQr";
import PaddleCheckout from "../components/PaddleCheckout";
import {
  DEFAULT_DEV_KEY,
  PLAN_PRICES,
  checkoutCard,
  checkoutCrypto,
  fetchBillingStatus,
  fetchCryptoInvoices,
  fetchCryptoNetworks,
  setBillingPlanMock,
  type BillingCryptoCheckoutResponse,
  type BillingCryptoNetwork,
  type BillingInvoice,
  type BillingStatus,
} from "../api";

const payablePlans = ["pro", "team", "business"] as const;

function formatCountdown(expiresAt: string | null | undefined): string | null {
  if (!expiresAt) return null;
  const ms = new Date(expiresAt).getTime() - Date.now();
  if (ms <= 0) return "Expired";
  const min = Math.floor(ms / 60000);
  const sec = Math.floor((ms % 60000) / 1000);
  return `${min}m ${sec}s`;
}

export default function Billing() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY);
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [networks, setNetworks] = useState<BillingCryptoNetwork[]>([]);
  const [invoices, setInvoices] = useState<BillingInvoice[]>([]);
  const [lastCheckout, setLastCheckout] = useState<BillingCryptoCheckoutResponse | null>(null);
  const [countdown, setCountdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [asset, setAsset] = useState<"usdc" | "usdt">("usdc");
  const [network, setNetwork] = useState("ethereum");

  const load = async () => {
    setLoading(true);
    setError(null);
    localStorage.setItem("uap_api_key", apiKey);
    try {
      const [s, inv] = await Promise.all([
        fetchBillingStatus(apiKey),
        fetchCryptoInvoices(apiKey),
      ]);
      setStatus(s);
      setInvoices(inv);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCryptoNetworks()
      .then((rows) => {
        setNetworks(rows);
        if (rows.length > 0) setNetwork(rows[0].id);
      })
      .catch(() => {
        setNetworks([
          { id: "ethereum", name: "Ethereum", chainId: 1, assets: ["usdc", "usdt"], rpcConfigured: false },
          { id: "polygon", name: "Polygon", chainId: 137, assets: ["usdc", "usdt"], rpcConfigured: false },
          { id: "base", name: "Base", chainId: 8453, assets: ["usdc", "usdt"], rpcConfigured: false },
          { id: "arbitrum", name: "Arbitrum One", chainId: 42161, assets: ["usdc", "usdt"], rpcConfigured: false },
          { id: "bsc", name: "BNB Smart Chain", chainId: 56, assets: ["usdc", "usdt"], rpcConfigured: false },
        ]);
      });
    load();
  }, []);

  useEffect(() => {
    const hasPending = invoices.some((i) => i.status === "pending");
    if (!hasPending && !lastCheckout?.expiresAt) return;
    const timer = window.setInterval(() => {
      fetchCryptoInvoices(apiKey).then(setInvoices).catch(() => undefined);
      fetchBillingStatus(apiKey).then(setStatus).catch(() => undefined);
      if (lastCheckout?.expiresAt) {
        setCountdown(formatCountdown(lastCheckout.expiresAt));
      }
    }, 5000);
    return () => window.clearInterval(timer);
  }, [apiKey, invoices, lastCheckout?.expiresAt]);

  useEffect(() => {
    if (!lastCheckout?.expiresAt) {
      setCountdown(null);
      return;
    }
    setCountdown(formatCountdown(lastCheckout.expiresAt));
  }, [lastCheckout?.expiresAt]);

  const selectedNetwork = networks.find((n) => n.id === network);
  const assetsForNetwork = selectedNetwork?.assets ?? ["usdc", "usdt"];

  useEffect(() => {
    if (!assetsForNetwork.includes(asset)) {
      setAsset(assetsForNetwork[0] as "usdc" | "usdt");
    }
  }, [asset, assetsForNetwork]);

  const onSetPlan = async (plan: string) => {
    setError(null);
    try {
      await setBillingPlanMock(apiKey, plan);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onPayCrypto = async (plan: string) => {
    setError(null);
    try {
      const resp = await checkoutCrypto(apiKey, plan, asset, network);
      setLastCheckout(resp);
      await load();
      if (resp.mode === "live" && resp.url.startsWith("ethereum:")) {
        window.open(resp.url, "_blank", "noopener,noreferrer");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onPayCard = async (plan: string) => {
    setError(null);
    try {
      const resp = await checkoutCard(apiKey, plan);
      if (resp.mode === "mock") {
        await load();
        return;
      }
      if (resp.url) window.location.href = resp.url;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const copyText = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      setError("Could not copy to clipboard");
    }
  };

  const showQr =
    lastCheckout &&
    (lastCheckout.mode === "live" || lastCheckout.mode === "mock-pending");

  return (
    <div className="layout-wide">
      <PaddleCheckout />
      <section>
        <header className="page-header" style={{ paddingTop: "1rem" }}>
          <p className="pill-label">Billing</p>
          <h1>Subscribe to NARNA Cloud</h1>
          <p>Card (Paddle) or stablecoin (USDC/USDT) on 5 chains. Bot confirms on-chain payments automatically.</p>
        </header>

        <div className="console-bar">
          <label>
            API Key
            <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="mono" />
          </label>
          <button type="button" className="btn btn-primary" onClick={load} disabled={loading}>
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {status && (
          <div className="card">
            <p><strong>Plan:</strong> <span className="mono">{status.plan}</span></p>
            <p><strong>Billing mode:</strong> <span className="mono">{status.billingMode}</span></p>
            <p><strong>Usage:</strong> {status.guInPeriod ?? 0} / {status.guLimit ?? "unlimited"} GU</p>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
              Events (legacy): {status.eventsInPeriod} / {status.eventsLimit ?? "unlimited"}
            </p>
          </div>
        )}

        <h2 style={{ marginTop: "1.5rem" }}>Pay by card</h2>
        <div className="pricing-grid">
          {payablePlans.map((p) => (
            <div key={`card-${p}`} className="card">
              <h3 style={{ textTransform: "capitalize" }}>{p}</h3>
              <p className="price">{PLAN_PRICES[p]}<span style={{ fontSize: "1rem" }}>/mo</span></p>
              <button type="button" className="btn btn-primary" onClick={() => onPayCard(p)} disabled={loading}>
                Pay with card
              </button>
            </div>
          ))}
        </div>

        <h2 style={{ marginTop: "1.5rem" }}>Pay by stablecoin</h2>
        <div className="console-bar" style={{ marginTop: "0.75rem" }}>
          <label>
            Network
            <select value={network} onChange={(e) => setNetwork(e.target.value)} style={selectStyle}>
              {networks.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.name} (chain {n.chainId}){n.rpcConfigured ? "" : " — RPC not set"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Asset
            <select value={asset} onChange={(e) => setAsset(e.target.value as "usdc" | "usdt")} style={selectStyle}>
              {assetsForNetwork.map((a) => (
                <option key={a} value={a}>{a.toUpperCase()}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="pricing-grid">
          {payablePlans.map((p) => (
            <div key={`crypto-${p}`} className={`card ${status?.plan === p ? "featured" : ""}`}>
              <h3 style={{ textTransform: "capitalize" }}>{p}</h3>
              <p className="price">{PLAN_PRICES[p]}<span style={{ fontSize: "1rem" }}>/mo</span></p>
              <button type="button" className="btn btn-primary" onClick={() => onPayCrypto(p)} disabled={loading}>
                Pay {asset.toUpperCase()} on {selectedNetwork?.name ?? network}
              </button>
              {status?.billingMode === "mock" && (
                <button type="button" className="btn btn-secondary" style={{ marginLeft: "0.5rem" }} onClick={() => onSetPlan(p)}>
                  Set {p} (dev)
                </button>
              )}
            </div>
          ))}
        </div>

        {lastCheckout && (
          <div className="card invoice-card" style={{ marginTop: "1.5rem" }}>
            <div className="invoice-card-grid">
              <div>
                <h3>Payment invoice</h3>
                <p><strong>Invoice:</strong> <span className="mono">{lastCheckout.invoiceId}</span></p>
                <p><strong>Amount:</strong> {lastCheckout.expectedAmount} {lastCheckout.asset.toUpperCase()}</p>
                <p><strong>Network:</strong> {lastCheckout.network}</p>
                {lastCheckout.expiresAt && (
                  <p>
                    <strong>Expires:</strong>{" "}
                    <span className={countdown === "Expired" ? "badge badge-fail" : "badge badge-wait"}>
                      {countdown ?? new Date(lastCheckout.expiresAt).toLocaleString()}
                    </span>
                  </p>
                )}
                <p>
                  <strong>Wallet:</strong>{" "}
                  <span className="mono">{lastCheckout.recipientWallet}</span>{" "}
                  <button type="button" className="btn btn-secondary" onClick={() => copyText(lastCheckout.recipientWallet)}>
                    Copy
                  </button>
                </p>
                <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                  Send the exact amount on the selected chain. Unpaid invoices expire automatically.
                </p>
              </div>
              {showQr && (
                <PaymentQr
                  payload={lastCheckout.qrPayload || lastCheckout.recipientWallet}
                  label={`Scan ${lastCheckout.asset.toUpperCase()} payment`}
                />
              )}
            </div>
          </div>
        )}

        {invoices.length > 0 && (
          <>
            <h2 style={{ marginTop: "1.5rem" }}>Invoice history</h2>
            <div className="card" style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Plan</th>
                    <th>Network</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Expires</th>
                    <th>Tx</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((inv) => (
                    <tr key={inv.invoiceId}>
                      <td className="mono">{inv.invoiceId}</td>
                      <td>{inv.plan}</td>
                      <td>{inv.network} / {inv.asset.toUpperCase()}</td>
                      <td>{inv.expectedAmount}</td>
                      <td>
                        <span className={`badge badge-${inv.status === "paid" ? "ok" : inv.status === "expired" ? "fail" : "wait"}`}>
                          {inv.status}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: "0.8rem" }}>
                        {inv.expiresAt ? inv.expiresAt.slice(0, 19) : "—"}
                      </td>
                      <td className="mono" style={{ fontSize: "0.8rem" }}>{inv.txHash ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

const selectStyle: CSSProperties = {
  background: "var(--bg)",
  border: "1px solid var(--border)",
  color: "var(--text)",
  padding: "0.5rem 0.75rem",
  borderRadius: 6,
  fontFamily: "inherit",
  minWidth: 240,
};
