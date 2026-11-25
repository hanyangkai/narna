// Paid model calls. Keys come only from env secrets — never from the client.
// Do not add keys in the repo. Prefer a cheap strong model so credit caps
// stay under net proceeds ($4.24 / $12.74).

export function configuredModel(env = {}) {
  if (env.OPENAI_API_KEY) {
    return { provider: "openai", model: env.AGENT_MODEL || "gpt-4o-mini", displayName: "GPT-4o mini" };
  }
  if (env.ANTHROPIC_API_KEY) {
    return { provider: "anthropic", model: env.AGENT_ANTHROPIC_MODEL || "claude-haiku-4-5", displayName: "Claude Haiku" };
  }
  if (env.AGENT_GEMINI_API_KEY) {
    return { provider: "gemini", model: env.AGENT_GEMINI_MODEL || "gemini-2.5-flash", displayName: "Gemini Flash" };
  }
  return null;
}

function safeMessages(body) {
  const system = String((body && body.system) || "You are Nana AI Agent. Complete multi-step tasks carefully.").slice(0, 8000);
  const raw = Array.isArray(body && body.messages) ? body.messages.slice(-30) : [];
  const messages = raw.map((m) => ({
    role: String(m.role || "user").slice(0, 16),
    content: String(m.content || "").slice(0, 12000),
  }));
  return { system, messages };
}

export async function completeAgent(env, body) {
  const cfg = configuredModel(env);
  if (!cfg) {
    const err = new Error("agent_models_not_configured");
    err.status = 503;
    throw err;
  }
  const { system, messages } = safeMessages(body);
  if (cfg.provider === "openai") {
    const content = await openaiComplete(env.OPENAI_API_KEY, cfg.model, system, messages);
    return { content, modelDisplayName: cfg.displayName, model: cfg.model };
  }
  if (cfg.provider === "anthropic") {
    const content = await anthropicComplete(env.ANTHROPIC_API_KEY, cfg.model, system, messages);
    return { content, modelDisplayName: cfg.displayName, model: cfg.model };
  }
  if (cfg.provider === "gemini") {
    const content = await geminiComplete(env.AGENT_GEMINI_API_KEY, cfg.model, system, messages);
    return { content, modelDisplayName: cfg.displayName, model: cfg.model };
  }
  const err = new Error("agent_models_not_configured");
  err.status = 503;
  throw err;
}

async function openaiComplete(key, model, system, messages) {
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      messages: [{ role: "system", content: system }, ...messages],
      max_tokens: 1024,
      temperature: 0.4,
    }),
  });
  if (!res.ok) {
    const err = new Error("upstream_openai_" + res.status);
    err.status = 502;
    throw err;
  }
  const data = await res.json();
  const content = (((data.choices || [])[0] || {}).message || {}).content || "";
  return String(content).trim();
}

async function anthropicComplete(key, model, system, messages) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      system,
      max_tokens: 1024,
      messages: messages.map((m) => ({
        role: m.role === "assistant" ? "assistant" : "user",
        content: m.content,
      })),
    }),
  });
  if (!res.ok) {
    const err = new Error("upstream_anthropic_" + res.status);
    err.status = 502;
    throw err;
  }
  const data = await res.json();
  const parts = data.content || [];
  return parts.map((p) => p.text || "").join("").trim();
}

async function geminiComplete(key, model, system, messages) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`;
  const contents = messages.map((m) => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: m.content }],
  }));
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: system }] },
      contents,
    }),
  });
  if (!res.ok) {
    const err = new Error("upstream_gemini_" + res.status);
    err.status = 502;
    throw err;
  }
  const data = await res.json();
  const parts = ((((data.candidates || [])[0] || {}).content || {}).parts) || [];
  return parts.map((p) => p.text || "").join("").trim();
}
