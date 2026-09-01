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
  sessionId?: string | null;
  totalGu?: number;
};

export type RunDetail = RunSummary & {
  events: Array<{
    eventId: string;
    eventType: string;
    sequence: number;
    ts: string;
    payload: Record<string, unknown>;
    eventHash?: string;
    sessionId?: string;
    executionUnitId?: string;
  }>;
  proofBundle?: Record<string, unknown> | null;
};

export type SessionSummary = {
  sessionId: string;
  logicalAgentId: string;
  state: string;
  totalGu: number;
  runCount: number;
  createdAt: string;
  closedAt: string | null;
  terminateReason: string | null;
};

export type SessionDetail = SessionSummary & {
  graph: { nodes?: Array<Record<string, unknown>> };
  runs: RunSummary[];
  units: Array<Record<string, unknown>>;
};

export type BillingStatus = {
  plan: string;
  periodStartAt: string;
  eventsInPeriod: number;
  eventsLimit: number | null;
  guInPeriod?: number;
  guLimit?: number | null;
  billingMode: string;
  cryptoMode?: string;
  mockPlanAllowed?: boolean;
  planExpiresAt?: string | null;
  adqaChecksInPeriod?: number;
  adqaSoftCap?: number | null;
  adqaHardCap?: number | null;
  seatCount?: number;
  email?: string | null;
  orgName?: string | null;
};

export type SignupResponse = {
  ok: boolean;
  orgId: number;
  email: string;
  name: string;
  plan: string;
  apiKey: string;
  keyPrefix: string;
  message: string;
};

export type AccountMe = {
  ok: boolean;
  orgId: number;
  email: string | null;
  name: string;
  plan: string;
  createdAt: string | null;
  planExpiresAt: string | null;
};

export type BillingCryptoNetwork = {
  id: string;
  name: string;
  chainId: number;
  assets: string[];
  rpcConfigured: boolean;
};

export type BillingCryptoConfig = {
  receiverWallet: string;
  cryptoMode: string;
  assets: string[];
  note?: string;
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
  seatCount?: number;
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

export async function fetchSessions(apiKey: string): Promise<SessionSummary[]> {
  const res = await fetch(`${API_BASE}/v1/sessions`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchSession(apiKey: string, sessionId: string): Promise<SessionDetail> {
  const res = await fetch(`${API_BASE}/v1/sessions/${sessionId}`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function purchasePackage(
  apiKey: string,
  packageId: string
): Promise<{
  packageId: string;
  guCharged: number;
  platformCutUsd: number;
  authorCutUsd: number;
  status: string;
  mode: string;
  checkoutUrl?: string | null;
  message: string;
}> {
  const res = await fetch(`${API_BASE}/v1/packages/purchase`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({ packageId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type PackageDetail = {
  packageId: string;
  name: string;
  version: string;
  provider: string;
  packageKind: string;
  license: string;
  disclaimer: string;
  packageHash: string;
  spec: Record<string, unknown>;
  priceUsd?: number;
  takeRateBps?: number;
  stars: number;
  downloads: number;
  publishedAt: string;
};

export async function fetchPackage(packageId: string): Promise<PackageDetail> {
  const res = await fetch(`${API_BASE}/v1/packages/${packageId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function verifyPackageSession(
  apiKey: string,
  sessionId: string
): Promise<{ packageId: string; status: string; mode: string; guCharged: number; message: string }> {
  const res = await fetch(`${API_BASE}/v1/packages/verify-session`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({ sessionId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchBillingStatus(apiKey: string): Promise<BillingStatus> {
  const res = await fetch(`${API_BASE}/v1/billing/status`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function signupAccount(email: string, name?: string): Promise<SignupResponse> {
  const res = await fetch(`${API_BASE}/v1/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, name: name || "" }),
  });
  if (!res.ok) {
    const text = await res.text();
    try {
      const j = JSON.parse(text) as { detail?: string };
      throw new Error(j.detail || text);
    } catch {
      throw new Error(text);
    }
  }
  return res.json();
}

export async function fetchAccountMe(apiKey: string): Promise<AccountMe> {
  const res = await fetch(`${API_BASE}/v1/auth/me`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchCryptoNetworks(): Promise<BillingCryptoNetwork[]> {
  const res = await fetch(`${API_BASE}/v1/billing/crypto/networks`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchCryptoConfig(): Promise<BillingCryptoConfig> {
  const res = await fetch(`${API_BASE}/v1/billing/crypto/config`);
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
  network: string,
  seats?: number
): Promise<BillingCryptoCheckoutResponse> {
  const res = await fetch(`${API_BASE}/v1/billing/crypto/checkout-session`, {
    method: "POST",
    headers: authHeaders(apiKey),
    body: JSON.stringify({
      plan,
      asset,
      network,
      ...(seats != null ? { seats } : {}),
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function checkoutCard(
  _apiKey: string,
  _plan: string
): Promise<BillingCheckoutResponse> {
  throw new Error(
    "Card / Stripe / Paddle checkout removed. Pay with USDC or USDT via /billing.",
  );
}

export type AgentAskResponse = {
  answer: string;
  dqs: number | null;
  guardian: string | null;
  decisionId: string;
  traceId?: string;
  mode?: string;
  verdict?: string;
  modelsUsed: string[];
  sources: Array<{ type: string; name: string }>;
  sessionId: string;
  plan?: string;
  agentTurnsInPeriod?: number;
  agentTurnsHardCap?: number | null;
  quota?: { message?: string };
  standard?: string;
  toolsUsed?: Array<{ tool: string; args?: Record<string, unknown>; result?: unknown }>;
  skillSaved?: { skillId?: string; name?: string } | null;
  challenge?: string | null;
  mockMode?: boolean;
};

function deviceId(): string {
  const key = "narna_device_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = "dev_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem(key, id);
  }
  return id;
}

export async function askNarna(
  message: string,
  opts?: {
    apiKey?: string;
    sessionId?: string;
    challenge?: boolean;
    files?: Array<{ name: string; text: string }>;
    showModels?: boolean;
    stream?: boolean;
    llmProvider?: string;
    llmApiKey?: string;
    llmBaseUrl?: string;
    llmModel?: string;
    mode?: string;
  }
): Promise<AgentAskResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Narna-Device": deviceId(),
  };
  if (opts?.apiKey) headers.Authorization = `Bearer ${opts.apiKey}`;
  if (opts?.showModels) headers["X-Narna-Show-Models"] = "1";
  const payload: Record<string, unknown> = {
    message,
    sessionId: opts?.sessionId,
    challenge: opts?.challenge ?? false,
    files: opts?.files ?? [],
  };
  if (opts?.mode) payload.mode = opts.mode;
  if (opts?.llmApiKey) {
    payload.llmApiKey = opts.llmApiKey;
    payload.llmProvider = opts.llmProvider || "openrouter";
    if (opts.llmBaseUrl) payload.llmBaseUrl = opts.llmBaseUrl;
    if (opts.llmModel) payload.llmModel = opts.llmModel;
  }

  if (opts?.stream !== false && typeof EventSource === "undefined") {
    // keep POST path below; EventSource can't POST — use fetch stream
  }

  if (opts?.stream !== false) {
    try {
      const res = await fetch(`${API_BASE}/v1/agent/ask/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      if (res.ok && res.body) {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        let result: AgentAskResponse | null = null;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const parts = buf.split("\n\n");
          buf = parts.pop() || "";
          for (const block of parts) {
            const lines = block.split("\n");
            let event = "message";
            let data = "";
            for (const line of lines) {
              if (line.startsWith("event:")) event = line.slice(6).trim();
              if (line.startsWith("data:")) data += line.slice(5).trim();
            }
            if (event === "result" && data) {
              result = JSON.parse(data) as AgentAskResponse;
            }
            if (event === "error" && data) {
              const err = JSON.parse(data) as { error?: string };
              throw new Error(err.error || "stream error");
            }
          }
        }
        if (result) return result;
      }
    } catch {
      // fall through to non-stream Ask
    }
  }

  const res = await fetch(`${API_BASE}/v1/agent/ask`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function recordAgentOutcome(
  decisionId: string,
  opts: {
    status?: string;
    lesson?: string;
    apiKey?: string;
  }
): Promise<{ ok: boolean }> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Narna-Device": deviceId(),
  };
  if (opts.apiKey) headers.Authorization = `Bearer ${opts.apiKey}`;
  const res = await fetch(`${API_BASE}/v1/agent/outcome`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      decisionId,
      status: opts.status ?? "success",
      lesson: opts.lesson,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listAgentSkills(apiKey?: string): Promise<
  Array<{ skillId: string; name: string; tags?: string[] }>
> {
  const headers: Record<string, string> = { "X-Narna-Device": deviceId() };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;
  const res = await fetch(`${API_BASE}/v1/agent/skills`, { headers });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.skills || [];
}

export type AgentModelsConfig = {
  ok: boolean;
  byoLlmAllowed: boolean;
  provider: string;
  baseUrl?: string | null;
  apiKeySet: boolean;
  apiKeyPreview?: string | null;
  modelCheap?: string | null;
  modelReason?: string | null;
  modelChallenge?: string | null;
  plan: string;
};

export async function fetchAgentModels(apiKey: string): Promise<AgentModelsConfig> {
  const res = await fetch(`${API_BASE}/v1/agent/models`, { headers: authHeaders(apiKey) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function saveAgentModels(
  apiKey: string,
  body: {
    provider: string;
    apiKey?: string;
    baseUrl?: string;
    modelCheap?: string;
    modelReason?: string;
    modelChallenge?: string;
  }
): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/v1/agent/models`, {
    method: "PUT",
    headers: authHeaders(apiKey),
    body: JSON.stringify(body),
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

export type DecisionPackageListing = {
  name: string;
  provider: string;
  version: string;
  kind: string;
  industry?: string | null;
  actions?: string[];
};

export type AdqaResult = {
  dqs?: number;
  attributes?: Record<string, number>;
  guardian?: string;
  constitution?: Record<string, string>;
  lessonsUsed?: unknown[];
  learningPrior?: Record<string, unknown> | null;
  decisionMemoryId?: string;
  standard?: string;
};

export type DecisionResult = {
  decision: string;
  recommendation?: string;
  action: string;
  riskScore?: number;
  riskBand?: string;
  reasons?: string[];
  requiredApprovals?: string[];
  evidence?: string[];
  context?: Record<string, unknown>;
  adqa?: AdqaResult;
  packageId?: string;
  provider?: string;
  evaluatedAt?: string;
};

export async function fetchDecisionPackages(
  industry?: string
): Promise<DecisionPackageListing[]> {
  const q = industry ? `?industry=${encodeURIComponent(industry)}` : "";
  const res = await fetch(`${API_BASE}/v1/dmarket/packages${q}`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.packages || [];
}

export async function evaluateDecision(body: {
  action: string;
  provider?: string;
  evidencePresent?: string[];
  context?: Record<string, unknown>;
  question?: string;
}): Promise<{ ok: boolean; result: DecisionResult }> {
  const res = await fetch(`${API_BASE}/v1/decision/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function checkAdqa(body: {
  action: string;
  provider?: string;
  evidencePresent?: string[];
  context?: Record<string, unknown>;
}): Promise<{ ok: boolean; adqa: AdqaResult; decisionResult: DecisionResult }> {
  const res = await fetch(`${API_BASE}/v1/adqa/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchGuardianStatus(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/v1/guardian/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function evaluateCapability(capability: string, agentId?: string) {
  const res = await fetch(`${API_BASE}/v1/capability/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ capability, agentId, profile: "guardian" }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function evaluateConstitution(action: string) {
  const res = await fetch(`${API_BASE}/v1/guardian/constitution/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchJurisdictions(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/v1/guardian/jurisdictions`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchIsolationPartners(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/v1/guardian/isolation/partners`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function certifyIsolationPartner(partner: string, attested = false) {
  const res = await fetch(`${API_BASE}/v1/guardian/isolation/certify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ partner, attested }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchPartnerCerts(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/v1/guardian/isolation/certs`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const DEFAULT_DEV_KEY = "uap_live_dev_local_key_change_in_prod";

export const PLAN_PRICES: Record<string, string> = {
  free: "$0",
  cloud: "$20",
  personal: "$20",
  pro: "$20",
  team: "$99/seat",
  business: "$199",
};
