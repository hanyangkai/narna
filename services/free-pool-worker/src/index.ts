/**
 * Nana AI free-pool proxy — Cloudflare Worker (free plan).
 * POST /v1/chat  → SSE {delta} stream. No message content logged.
 *
 * Upstream order: Workers AI (gpt-oss/Gemma/Llama/Qwen) → Gemini free (skip EEA/UK/CH)
 * → Groq (if key) → OpenRouter :free → Z.AI GLM Flash overflow.
 */

import { checkAndBump } from "./limits";
import { streamWithFallback, type ChatMessage } from "./upstreams";

export interface Env {
  LIMITS: KVNamespace;
  AI: Ai;
  GROQ_API_KEY?: string;
  OPENROUTER_API_KEY?: string;
  GEMINI_API_KEY?: string;
  ZAI_API_KEY?: string;
  DAILY_MSG_LIMIT_PER_DEVICE?: string;
  GLOBAL_DAILY_MSG_CAP?: string;
  MAX_TOKENS?: string;
  OPENROUTER_FREE_MODELS?: string;
  GROQ_MODEL?: string;
  GEMINI_MODEL?: string;
  ZAI_MODEL?: string;
  ZAI_BASE_URL?: string;
  WORKERS_AI_MODELS?: string;
  FREE_POOL_PAUSED?: string;
  /** When "1", require X-Device-Check-Token (DeviceCheck). Soft by default. */
  REQUIRE_DEVICE_CHECK?: string;
}

function corsHeaders(): HeadersInit {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers":
      "Content-Type, X-Device-Id, X-Device-Check-Token, X-Region-Hint",
  };
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    const url = new URL(request.url);
    if (request.method === "GET" && url.pathname === "/health") {
      return json(200, { ok: true, service: "nana-free-pool" });
    }

    if (request.method !== "POST" || url.pathname !== "/v1/chat") {
      return json(404, { error: "not_found" });
    }

    let body: { deviceId?: string; messages?: ChatMessage[]; regionHint?: string };
    try {
      body = (await request.json()) as typeof body;
    } catch {
      return json(400, { error: "invalid_json" });
    }

    const deviceId = String(
      body.deviceId || request.headers.get("X-Device-Id") || ""
    ).trim();
    if (!deviceId || deviceId.length < 8) {
      return json(400, { error: "device_id_required" });
    }

    const deviceCheck = (request.headers.get("X-Device-Check-Token") || "").trim();
    if ((env.REQUIRE_DEVICE_CHECK || "").trim() === "1" && !deviceCheck) {
      return json(401, { error: "device_check_required" });
    }
    // Token is accepted and folded into the KV counter key when present.
    // Full Apple DeviceCheck verification needs Apple server API keys — optional later.

    const messages = Array.isArray(body.messages) ? body.messages : [];
    if (!messages.length) {
      return json(400, { error: "messages_required" });
    }

    const safeMessages: ChatMessage[] = messages.slice(-20).map((m) => ({
      role: String(m.role || "user").slice(0, 16),
      content: String(m.content || "").slice(0, 8000),
    }));

    const ip =
      request.headers.get("CF-Connecting-IP") ||
      request.headers.get("X-Forwarded-For")?.split(",")[0]?.trim() ||
      "unknown";

    const regionHint =
      body.regionHint ||
      request.headers.get("X-Region-Hint") ||
      request.headers.get("CF-IPCountry") ||
      "";

    const limitKey = deviceCheck
      ? `dc:${await hashShort(deviceCheck)}`
      : deviceId;

    const limit = await checkAndBump(env, limitKey, ip);
    if (!limit.ok) {
      console.log(
        JSON.stringify({
          event: "limit",
          error: limit.error,
          deviceHash: await hashShort(deviceId),
          // no message content
        })
      );
      return json(limit.status, {
        error: limit.error,
        message:
          limit.error === "daily_limit"
            ? "daily limit reached"
            : limit.error,
      });
    }

    const upstream = await streamWithFallback(env, safeMessages, { regionHint });
    if (!upstream.ok) {
      console.log(
        JSON.stringify({
          event: "upstream_fail",
          error: upstream.error,
          deviceHash: await hashShort(deviceId),
        })
      );
      return json(502, { error: "upstream_unavailable" });
    }

    console.log(
      JSON.stringify({
        event: "chat_ok",
        engine: upstream.engine,
        deviceHash: await hashShort(deviceId),
        region: regionHint || "unknown",
        approxPromptChars: safeMessages.reduce((n, m) => n + m.content.length, 0),
      })
    );

    return new Response(upstream.stream, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "X-Nana-Engine": upstream.engine,
        ...corsHeaders(),
      },
    });
  },
};

async function hashShort(value: string): Promise<string> {
  const data = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", data);
  const bytes = new Uint8Array(digest);
  return Array.from(bytes.slice(0, 6))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
