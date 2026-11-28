// Nana AI free-pool Worker. Scaffold only — do not deploy without owner approval.
// Keys stay in Worker secrets. The iOS app never embeds them.

const router = require("./router.js");

const FETCH_TIMEOUT_MS = 5000;
const WORKERS_AI_TIMEOUT_MS = 6000;

// Circuit breaker: a model that failed (timeout, 4xx/5xx, empty reply) is skipped for a few minutes.
// Held in isolate memory and mirrored to one KV key so other isolates pick it up. KV is only
// written when a route newly trips, so it stays far below the free-plan write limit.
const BREAKER_MS = 5 * 60 * 1000;
const BREAKER_KEY = "breaker:v1";
const breaker = { until: new Map(), loadedAt: 0 };

function breakerId(route) { return route.provider + ":" + route.id; }
function breakerIsOpen(route) {
  const until = breaker.until.get(breakerId(route));
  return Boolean(until && until > Date.now());
}
async function breakerLoad(env) {
  if (Date.now() - breaker.loadedAt < 30000) return;
  breaker.loadedAt = Date.now();
  try {
    const raw = await env.QUOTA.get(BREAKER_KEY);
    if (!raw) return;
    for (const [k, v] of Object.entries(JSON.parse(raw))) {
      if (v > (breaker.until.get(k) || 0)) breaker.until.set(k, v);
    }
  } catch { /* breaker is best effort */ }
}
async function breakerTrip(env, route) {
  const now = Date.now();
  const id = breakerId(route);
  if ((breaker.until.get(id) || 0) > now) return;
  breaker.until.set(id, now + BREAKER_MS);
  const live = {};
  for (const [k, v] of breaker.until) if (v > now) live[k] = v;
  try { await env.QUOTA.put(BREAKER_KEY, JSON.stringify(live), { expirationTtl: 600 }); } catch { /* ignore */ }
}

export default {
  async fetch(request, env, ctx) {
    return handle(request, env);
  },
};

// Wrangler wants ESM default export; also support CJS tests by keeping helpers in router.js.
// This file is ESM-shaped via wrangler; the require above works in the bundled graph.
// If wrangler is not used, this file is documentation + a complete handler.

async function handle(request, env) {
  const url = new URL(request.url);
  if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/health")) {
    return json({ ok: true, service: "nana-free-pool" });
  }
  if (request.method !== "POST" || url.pathname !== "/v1/chat") {
    return json({ error: "Not found" }, 404);
  }

  const deviceId = await identifyDevice(request, env);
  if (!deviceId) {
    return json({ error: "This device could not be verified." }, 401);
  }

  const limit = router.dailyLimit(env);
  const key = router.quotaKey(deviceId);
  const used = Number.parseInt((await env.QUOTA.get(key)) || "0", 10) || 0;
  if (used >= limit) {
    return json({ error: "You have used today's " + limit + " free cloud messages. Try again tomorrow, or use on-device chat if it is available.", remaining: 0 }, 429);
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "Invalid JSON body." }, 400);
  }
  const messages = Array.isArray(body.messages) ? body.messages : [];
  if (messages.length === 0) return json({ error: "messages is required." }, 400);

  const region = body.region || request.headers.get("X-Device-Region") || "";
  const cfCountry = (request.cf && request.cf.country) || "";

  const slowProviders = new Set();
  await breakerLoad(env);
  const result = await router.completeWithFallback({
    env,
    region,
    cfCountry,
    isOpen: breakerIsOpen,
    onFailure: (route, res) => (res && res.status === 400 ? null : breakerTrip(env, route)),
    call: async (route) => {
      // If a provider timed out once in this request, skip its remaining models.
      if (slowProviders.has(route.provider)) return { ok: false, status: 503, error: "Provider skipped after timeout." };
      const r = await callProvider(route, env, body.system || "", messages);
      if (r && r.timedOut) slowProviders.add(route.provider);
      return r;
    },
  });

  if (!result.ok) {
    const status = router.isRetryableStatus(result.status) ? 503 : (result.status || 503);
    return json({ error: result.error || "All free-pool providers failed." }, status);
  }

  const next = used + 1;
  await env.QUOTA.put(key, String(next), { expirationTtl: 172800 });
  return json({
    content: result.content,
    model: result.model,
    modelDisplayName: result.modelDisplayName,
    remaining: Math.max(0, limit - next),
  });
}

async function identifyDevice(request, env) {
  const attest = request.headers.get("X-App-Attest-Assertion");
  const keyId = request.headers.get("X-App-Attest-Key-Id");
  const dc = request.headers.get("X-DeviceCheck-Token");
  const debugId = request.headers.get("X-Debug-Device-Id");
  if (attest && keyId) return "attest:" + keyId;
  if (dc) return "dc:" + await sha256(dc);
  if (env.DEV_ALLOW_UNATTESTED === "1" && debugId) return "debug:" + debugId;
  return null;
}

async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function callProvider(route, env, system, messages) {
  try {
    if (route.provider === "workersai") {
      return await callWorkersAI(route, env, system, messages);
    }
    const { url, headers, body } = requestFor(route, env, system, messages);
    // Hard per-provider timeout so one hung upstream cannot stall the whole fallback chain.
    const resp = await fetch(url, { method: "POST", headers, body: JSON.stringify(body), signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
    const text = await resp.text();
    let parsed = {};
    try { parsed = JSON.parse(text); } catch { /* ignore */ }
    if (router.isRetryableStatus(resp.status)) {
      return { ok: false, status: resp.status, error: errorMessage(parsed, text, resp.status) };
    }
    if (!resp.ok) {
      return { ok: false, status: resp.status, error: errorMessage(parsed, text, resp.status) };
    }
    const content = extractContent(parsed);
    if (!content) return { ok: false, status: 502, error: "Empty model response." };
    return { ok: true, content };
  } catch (err) {
    const timedOut = Boolean(err && (err.name === "TimeoutError" || err.name === "AbortError" || /timed out/i.test(err.message || "")));
    return { ok: false, status: 503, timedOut, error: (err && err.message) || "Provider call failed." };
  }
}

function requestFor(route, env, system, messages) {
  const chat = openAIMessages(system, messages);
  if (route.provider === "groq") {
    return {
      url: "https://api.groq.com/openai/v1/chat/completions",
      headers: { Authorization: "Bearer " + env.GROQ_API_KEY, "Content-Type": "application/json" },
      body: { model: route.id, messages: chat },
    };
  }
  if (route.provider === "google") {
    return {
      url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
      headers: { Authorization: "Bearer " + env.GEMINI_API_KEY, "Content-Type": "application/json" },
      body: { model: route.id, messages: chat },
    };
  }
  if (route.provider === "openrouter") {
    return {
      url: "https://openrouter.ai/api/v1/chat/completions",
      headers: {
        Authorization: "Bearer " + env.OPENROUTER_API_KEY,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://narna.org",
        "X-Title": "Nana AI",
      },
      body: { model: route.id, messages: chat },
    };
  }
  if (route.provider === "zai") {
    const base = (env.ZAI_BASE_URL || "https://api.z.ai/api/paas/v4").replace(/\/$/, "");
    return {
      url: base + "/chat/completions",
      headers: { Authorization: "Bearer " + env.ZAI_API_KEY, "Content-Type": "application/json" },
      body: { model: route.id, messages: chat },
    };
  }
  throw new Error("Unknown provider " + route.provider);
}

async function callWorkersAI(route, env, system, messages) {
  if (!env.AI || typeof env.AI.run !== "function") {
    return { ok: false, status: 503, error: "Workers AI binding is not available." };
  }
  const result = await Promise.race([
    env.AI.run(route.id, { messages: openAIMessages(system, messages) }),
    new Promise((_, reject) => setTimeout(() => reject(new Error("Workers AI timed out.")), WORKERS_AI_TIMEOUT_MS)),
  ]);
  // Workers AI returns either the legacy { response } shape or OpenAI chat.completion (gpt-oss, llama 3.x, qwen).
  const choice = result && result.choices && result.choices[0];
  const content = (result && (result.response || result.content || (result.result && result.result.response)))
    || (choice && choice.message && choice.message.content)
    || "";
  if (!content) return { ok: false, status: 502, error: "Empty Workers AI response." };
  return { ok: true, content: String(content).trim() };
}

function openAIMessages(system, messages) {
  const out = [];
  if (system) out.push({ role: "system", content: system });
  for (const m of messages) {
    out.push({ role: m.role === "assistant" ? "assistant" : "user", content: String(m.content || "") });
  }
  return out;
}

function extractContent(parsed) {
  const choice = parsed && parsed.choices && parsed.choices[0];
  if (choice && choice.message && choice.message.content) return String(choice.message.content).trim();
  if (parsed && parsed.content) return String(parsed.content).trim();
  return "";
}

function errorMessage(parsed, text, status) {
  return (parsed && (parsed.error && (parsed.error.message || parsed.error))) || parsed.message || text.slice(0, 200) || ("HTTP " + status);
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });
}
