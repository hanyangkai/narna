const API_BASE = import.meta.env.VITE_API_URL || "";

export type RunSummary = {
  runId: string;
  agentId: string;
  agentName: string;
  state: string;
  tipHash: string;
  trustScore: number | null;
  eventCount: number;
  updatedAt: string;
};

export type RunDetail = RunSummary & {
  events: Array<{
    eventId: string;
    eventType: string;
    sequence: number;
    ts: string;
    payload: Record<string, unknown>;
    eventHash?: string;
  }>;
  proofBundle?: Record<string, unknown> | null;
};

export type BillingStatus = {
  plan: string;
  periodStartAt: string;
  eventsInPeriod: number;
  eventsLimit: number | null;
  billingMode: string;
};

export type BillingCryptoNetwork = {
  id: string;
  name: string;
  chainId: number;
  assets: string[];
  rpcConfigured: boolean;
};

export type BillingCryptoCheckoutResponse = {
  ok: boolean;
  url: string;
  mode: string;
  invoiceId: string;
  plan: string;
  asset: string;
  network: string;
  recipientWallet: string;
  expectedAmount: string;
  expiresAt: string;
  qrPayload: string;
};

export type BillingInvoice = {
  invoiceId: string;
  kind: string;
  plan: string;
  asset: string;
  network: string;
  recipientWallet: string;
  expectedAmount: string;
  status: string;
  txHash: string | null;
  createdAt: string;
  expiresAt: string | null;
  paidAt: string | null;
};

export type BillingCheckoutResponse = {
  ok: boolean;
  url: string;
  mode: string;
};

function authHeaders(apiKey: string): HeadersInit {
  return {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  };
}

export async function fetchRuns(apiKey: string): Promise<RunSummary[]> {
  const res = await fetch(`${API_BASE}/v1/runs`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchRun(apiKey: string, runId: string): Promise<RunDetail> {
  const res = await fetch(`${API_BASE}/v1/runs/${runId}`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchBillingStatus(apiKey: string): Promise<BillingStatus> {
  const res = await fetch(`${API_BASE}/v1/billing/status`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchCryptoNetworks(): Promise<BillingCryptoNetwork[]> {
  const res = await fetch(`${API_BASE}/v1/billing/crypto/networks`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchCryptoInvoices(apiKey: string): Promise<BillingInvoice[]> {
  const res = await fetch(`${API_BASE}/v1/billing/crypto/invoices`, {
    headers: authHeaders(apiKey),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function setBillingPlanMock(apiKey: string, plan: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/billing/mock/set-plan`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({ plan }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function checkoutCrypto(
  apiKey: string,
  plan: string,
  asset: "usdc" | "usdt",
  network: string
): Promise<BillingCryptoCheckoutResponse> {
  const res = await fetch(`${API_BASE}/v1/billing/crypto/checkout-session`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({ plan, asset, network }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function checkoutCard(
  apiKey: string,
  plan: string
): Promise<BillingCheckoutResponse> {
  const res = await fetch(`${API_BASE}/v1/billing/checkout-session`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({ plan }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/v1/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export const DEFAULT_DEV_KEY = "uap_live_dev_local_key_change_in_prod";

export const PLAN_PRICES: Record<string, string> = {
  free: "$0",
  pro: "$19",
  team: "$49",
  business: "$199",
};
