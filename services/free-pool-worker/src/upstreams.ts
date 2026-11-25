/** Ordered free upstreams — secrets only from env, never logged content. */

export interface ChatMessage {
  role: string;
  content: string;
}

export interface UpstreamEnv {
  AI: Ai;
  GROQ_API_KEY?: string;
  OPENROUTER_API_KEY?: string;
  GEMINI_API_KEY?: string;
  ZAI_API_KEY?: string;
  OPENROUTER_FREE_MODELS?: string;
  GROQ_MODEL?: string;
  GEMINI_MODEL?: string;
  ZAI_MODEL?: string;
  ZAI_BASE_URL?: string;
  WORKERS_AI_MODELS?: string;
  MAX_TOKENS?: string;
}

/** Regions where Google free Gemini API requires Paid Services. */
export const GEMINI_SKIP_REGIONS = new Set(["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS", "LI", "NO", "CH", "GB", "UK"]);

export function shouldSkipGemini(regionHint?: string | null): boolean {
  if (!regionHint) return false;
  return GEMINI_SKIP_REGIONS.has(regionHint.trim().toUpperCase());
}

function maxTokens(env: UpstreamEnv): number {
  return Math.min(Number(env.MAX_TOKENS || "512"), 1024);
}

export type StreamResult =
  | { ok: true; stream: ReadableStream<Uint8Array>; engine: string }
  | { ok: false; error: string };

function workersAiModels(env: UpstreamEnv): string[] {
  return (
    env.WORKERS_AI_MODELS ||
    "@cf/openai/gpt-oss-120b,@cf/openai/gpt-oss-20b,@cf/google/gemma-2-9b-it,@cf/meta/llama-3.1-8b-instruct,@cf/qwen/qwen1.5-7b-chat-awq"
  )
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

async function tryWorkersAI(env: UpstreamEnv, messages: ChatMessage[]): Promise<StreamResult> {
  const models = workersAiModels(env);
  let lastErr = "workers_ai_failed";
  for (const model of models) {
    try {
      const result = await env.AI.run(model as keyof AiModels, {
        messages: messages.map((m) => ({ role: m.role, content: m.content })),
        stream: true,
        max_tokens: maxTokens(env),
      });
      if (result instanceof ReadableStream) {
        return {
          ok: true,
          stream: result as ReadableStream<Uint8Array>,
          engine: model.includes("gpt-oss") ? `workers-ai:gpt-oss` : `workers-ai:${model}`,
        };
      }
      const text =
        typeof result === "object" && result && "response" in result
          ? String((result as { response?: string }).response || "")
          : JSON.stringify(result);
      return {
        ok: true,
        stream: sseFromText(text),
        engine: model.includes("gpt-oss") ? `workers-ai:gpt-oss` : `workers-ai:${model}`,
      };
    } catch (e) {
      lastErr = `workers_ai:${String(e).slice(0, 80)}`;
    }
  }
  return { ok: false, error: lastErr };
}

async function tryGemini(
  env: UpstreamEnv,
  messages: ChatMessage[],
  regionHint?: string | null
): Promise<StreamResult> {
  if (shouldSkipGemini(regionHint)) {
    return { ok: false, error: "gemini_skipped_eea" };
  }
  const key = (env.GEMINI_API_KEY || "").trim();
  if (!key) return { ok: false, error: "gemini_missing_key" };

  const model = env.GEMINI_MODEL || "gemini-3.8-flash";
  // Map chat roles → Gemini contents
  const contents = messages
    .filter((m) => m.role !== "system")
    .map((m) => ({
      role: m.role === "assistant" ? "model" : "user",
      parts: [{ text: m.content }],
    }));
  const system = messages.find((m) => m.role === "system")?.content;

  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:streamGenerateContent?alt=sse&key=${encodeURIComponent(key)}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents,
        systemInstruction: system ? { parts: [{ text: system }] } : undefined,
        generationConfig: { maxOutputTokens: maxTokens(env) },
      }),
    });
    if (!res.ok || !res.body) {
      return { ok: false, error: `gemini_http_${res.status}` };
    }
    return { ok: true, stream: geminiToNormalizedSse(res.body), engine: `gemini:${model}` };
  } catch (e) {
    return { ok: false, error: `gemini:${String(e).slice(0, 80)}` };
  }
}

async function tryGroq(env: UpstreamEnv, messages: ChatMessage[]): Promise<StreamResult> {
  const key = (env.GROQ_API_KEY || "").trim();
  if (!key) return { ok: false, error: "groq_missing_key" };
  const model = env.GROQ_MODEL || "openai/gpt-oss-20b";
  try {
    const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model,
        stream: true,
        max_tokens: maxTokens(env),
        messages,
      }),
    });
    if (res.status === 429 || res.status === 503) {
      return { ok: false, error: `groq_http_${res.status}` };
    }
    if (!res.ok || !res.body) {
      return { ok: false, error: `groq_http_${res.status}` };
    }
    return { ok: true, stream: openaiToNormalizedSse(res.body), engine: `groq:${model}` };
  } catch (e) {
    return { ok: false, error: `groq:${String(e).slice(0, 80)}` };
  }
}

async function tryOpenRouterFree(env: UpstreamEnv, messages: ChatMessage[]): Promise<StreamResult> {
  const key = (env.OPENROUTER_API_KEY || "").trim();
  if (!key) return { ok: false, error: "openrouter_missing_key" };
  const models = (
    env.OPENROUTER_FREE_MODELS ||
    "openai/gpt-oss-20b:free,google/gemma-2-9b-it:free,meta-llama/llama-3.2-3b-instruct:free"
  )
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  let lastErr = "openrouter_failed";
  for (const model of models) {
    try {
      const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${key}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://narna.org",
          "X-Title": "Nana AI Free Pool",
        },
        body: JSON.stringify({
          model,
          stream: true,
          max_tokens: maxTokens(env),
          messages,
        }),
      });
      if (res.status === 429 || res.status === 503) {
        lastErr = `openrouter_http_${res.status}`;
        continue;
      }
      if (!res.ok || !res.body) {
        lastErr = `openrouter_http_${res.status}`;
        continue;
      }
      return { ok: true, stream: openaiToNormalizedSse(res.body), engine: `openrouter:${model}` };
    } catch (e) {
      lastErr = `openrouter:${String(e).slice(0, 80)}`;
    }
  }
  return { ok: false, error: lastErr };
}

async function tryZai(env: UpstreamEnv, messages: ChatMessage[]): Promise<StreamResult> {
  const key = (env.ZAI_API_KEY || "").trim();
  if (!key) return { ok: false, error: "zai_missing_key" };
  const model = env.ZAI_MODEL || "glm-4.7-flash";
  const base = (env.ZAI_BASE_URL || "https://api.z.ai/api/paas/v4").replace(/\/$/, "");
  try {
    const res = await fetch(`${base}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model,
        stream: true,
        max_tokens: maxTokens(env),
        messages,
      }),
    });
    if (res.status === 429 || res.status === 503) {
      return { ok: false, error: `zai_http_${res.status}` };
    }
    if (!res.ok || !res.body) {
      return { ok: false, error: `zai_http_${res.status}` };
    }
    return { ok: true, stream: openaiToNormalizedSse(res.body), engine: `zai:${model}` };
  } catch (e) {
    return { ok: false, error: `zai:${String(e).slice(0, 80)}` };
  }
}

export async function streamWithFallback(
  env: UpstreamEnv,
  messages: ChatMessage[],
  opts?: { regionHint?: string | null }
): Promise<StreamResult> {
  const regionHint = opts?.regionHint;
  const chain: Array<() => Promise<StreamResult>> = [
    () => tryWorkersAI(env, messages),
    () => tryGemini(env, messages, regionHint),
    () => tryGroq(env, messages),
    () => tryOpenRouterFree(env, messages),
    () => tryZai(env, messages),
  ];
  const errors: string[] = [];
  for (const fn of chain) {
    const out = await withTimeout(fn(), 45_000);
    if (out.ok) return out;
    errors.push(out.error);
  }
  return { ok: false, error: errors.join("|") };
}

function withTimeout<T extends StreamResult>(p: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve) => {
    const t = setTimeout(() => {
      resolve({ ok: false, error: "timeout" } as T);
    }, ms);
    p.then((v) => {
      clearTimeout(t);
      resolve(v);
    }).catch((e) => {
      clearTimeout(t);
      resolve({ ok: false, error: `timeout_err:${String(e).slice(0, 40)}` } as T);
    });
  });
}

function sseFromText(text: string): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      controller.enqueue(enc.encode(`data: ${JSON.stringify({ delta: text })}\n\n`));
      controller.enqueue(enc.encode("data: [DONE]\n\n"));
      controller.close();
    },
  });
}

/** Convert OpenAI-style SSE into `{delta}` normalized SSE. */
function openaiToNormalizedSse(body: ReadableStream<Uint8Array>): ReadableStream<Uint8Array> {
  const decoder = new TextDecoder();
  const encoder = new TextEncoder();
  let buffer = "";
  return new ReadableStream({
    async start(controller) {
      const reader = body.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const payload = trimmed.slice(5).trim();
            if (payload === "[DONE]") {
              controller.enqueue(encoder.encode("data: [DONE]\n\n"));
              continue;
            }
            try {
              const obj = JSON.parse(payload) as {
                choices?: Array<{ delta?: { content?: string } }>;
              };
              const delta = obj.choices?.[0]?.delta?.content;
              if (delta) {
                controller.enqueue(encoder.encode(`data: ${JSON.stringify({ delta })}\n\n`));
              }
            } catch {
              /* skip malformed */
            }
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
      } catch (e) {
        controller.error(e);
      }
    },
  });
}

function geminiToNormalizedSse(body: ReadableStream<Uint8Array>): ReadableStream<Uint8Array> {
  const decoder = new TextDecoder();
  const encoder = new TextEncoder();
  let buffer = "";
  return new ReadableStream({
    async start(controller) {
      const reader = body.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const payload = trimmed.slice(5).trim();
            if (!payload) continue;
            try {
              const obj = JSON.parse(payload) as {
                candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }>;
              };
              const text = obj.candidates?.[0]?.content?.parts?.map((p) => p.text || "").join("") || "";
              if (text) {
                controller.enqueue(encoder.encode(`data: ${JSON.stringify({ delta: text })}\n\n`));
              }
            } catch {
              /* skip */
            }
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
      } catch (e) {
        controller.error(e);
      }
    },
  });
}
