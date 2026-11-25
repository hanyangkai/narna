/** Ordered free upstreams — secrets only from env, never logged content. */

export interface ChatMessage {
  role: string;
  content: string;
}

export interface UpstreamEnv {
  AI: Ai;
  GROQ_API_KEY?: string;
  OPENROUTER_API_KEY?: string;
  OPENROUTER_FREE_MODELS?: string;
  GROQ_MODEL?: string;
  MAX_TOKENS?: string;
}

function maxTokens(env: UpstreamEnv): number {
  return Math.min(Number(env.MAX_TOKENS || "512"), 1024);
}

export type StreamResult =
  | { ok: true; stream: ReadableStream<Uint8Array>; engine: string }
  | { ok: false; error: string };

async function tryWorkersAI(env: UpstreamEnv, messages: ChatMessage[]): Promise<StreamResult> {
  try {
    const result = await env.AI.run("@cf/meta/llama-3.1-8b-instruct" as keyof AiModels, {
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      stream: true,
      max_tokens: maxTokens(env),
    });
    if (result instanceof ReadableStream) {
      return { ok: true, stream: result as ReadableStream<Uint8Array>, engine: "workers-ai" };
    }
    // Non-stream object — wrap as single SSE chunk
    const text =
      typeof result === "object" && result && "response" in result
        ? String((result as { response?: string }).response || "")
        : JSON.stringify(result);
    return { ok: true, stream: sseFromText(text), engine: "workers-ai" };
  } catch (e) {
    return { ok: false, error: `workers_ai:${String(e).slice(0, 80)}` };
  }
}

async function tryGroq(env: UpstreamEnv, messages: ChatMessage[]): Promise<StreamResult> {
  const key = (env.GROQ_API_KEY || "").trim();
  if (!key) return { ok: false, error: "groq_missing_key" };
  const model = env.GROQ_MODEL || "llama-3.1-8b-instant";
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
  const models = (env.OPENROUTER_FREE_MODELS || "meta-llama/llama-3.2-3b-instruct:free")
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

export async function streamWithFallback(
  env: UpstreamEnv,
  messages: ChatMessage[]
): Promise<StreamResult> {
  const chain = [tryWorkersAI, tryGroq, tryOpenRouterFree];
  const errors: string[] = [];
  for (const fn of chain) {
    const out = await fn(env, messages);
    if (out.ok) return out;
    errors.push(out.error);
  }
  return { ok: false, error: errors.join("|") };
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
                controller.enqueue(
                  encoder.encode(`data: ${JSON.stringify({ delta })}\n\n`)
                );
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
