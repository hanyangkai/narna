import { verifyStoreKitJws } from "./jws.js";
import { consumeCredits, refundCredits } from "./credits.js";
import { completeAgent } from "./upstream.js";
import { configuredModel } from "./upstream.js";

export default {
  async fetch(request, env) {
    return handleRequest(request, env);
  },
};

export async function handleRequest(request, env = {}) {
  const url = new URL(request.url);
  if (request.method === "GET" && (url.pathname === "/health" || url.pathname === "/")) {
    return json(200, { ok: true, service: "nana-agent-proxy", modelsConfigured: Boolean(configuredModel(env)) });
  }
  if (request.method === "POST" && url.pathname === "/v1/agent") {
    return handleAgent(request, env);
  }
  return json(404, { error: "not_found" });
}

async function handleAgent(request, env) {
  const jws = request.headers.get("X-StoreKit-JWS") || "";
  if (!jws) return json(401, { error: "missing_storekit_jws" });

  let tx;
  try {
    tx = await verifyStoreKitJws(jws, env);
  } catch (e) {
    return json(statusOf(e, 401), { error: e.message || "invalid_jws" });
  }

  let body = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  let reservation;
  try {
    reservation = await consumeCredits(env, tx, body);
  } catch (e) {
    const status = statusOf(e, 403);
    return json(status, { error: e.message || "credits", creditsRemaining: e.creditsRemaining ?? 0 });
  }

  try {
    const reply = await completeAgent(env, body);
    if (!reply.content) {
      await refundCredits(env, reservation.key, reservation.cost);
      return json(502, { error: "empty_upstream" });
    }
    return json(200, {
      content: reply.content,
      modelDisplayName: reply.modelDisplayName,
      creditsRemaining: reservation.remaining,
    });
  } catch (e) {
    await refundCredits(env, reservation.key, reservation.cost).catch(() => {});
    return json(statusOf(e, 502), { error: e.message || "upstream_failed" });
  }
}

function statusOf(e, fallback) {
  const n = Number(e && e.status);
  return Number.isFinite(n) && n >= 400 && n < 600 ? n : fallback;
}

function json(status, obj) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}
