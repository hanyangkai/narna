// Pure routing for the Nana AI free pool. No secrets in this file.
// Fail over on 429 and 503. Skip Google unpaid API for EEA / UK / CH.

const GOOGLE_RESTRICTED_REGIONS = new Set([
  "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
  "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
  "SI", "ES", "SE", "IS", "LI", "NO", "GB", "UK", "CH",
]);

const DEFAULTS = {
  // Primary gpt-oss path: Workers AI binding, no external key.
  workersaiGptOss: [
    "@cf/openai/gpt-oss-120b",
    "@cf/openai/gpt-oss-20b",
  ],
  // Optional overflow when GROQ_API_KEY is set; skipped otherwise.
  groq: ["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
  google: [
    "gemini-3.8-flash",
    "gemini-3.8-flash-lite",
    "gemini-3.6-flash",
    "gemma-4-31b-it",
    "gemma-4-26b-it",
  ],
  workersaiOther: [
    "@cf/meta/llama-3.1-8b-instruct-fp8-fast",
    "@cf/google/gemma-4-26b-a4b-it",
    "@cf/qwen/qwen3.8-27b",
  ],
  openrouter: [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "openrouter/free",
  ],
  zai: ["glm-4.7-flash"],
};
DEFAULTS.workersai = DEFAULTS.workersaiGptOss.concat(DEFAULTS.workersaiOther);

const DISPLAY_FAMILY = [
  [/gemini/i, "Gemini Flash"],
  [/gpt-oss|gpt_oss/i, "GPT-OSS"],
  [/gemma/i, "Gemma"],
  [/llama/i, "Llama"],
  [/qwen/i, "Qwen"],
  [/glm/i, "GLM"],
];

function parseList(raw, fallback) {
  if (typeof raw === "string" && raw.trim()) {
    return raw.split(",").map((s) => s.trim()).filter(Boolean);
  }
  return fallback.slice();
}

function enabledProviders(env) {
  const raw = (env && env.ENABLED_PROVIDERS) || "groq,google,workersai,openrouter,zai";
  return new Set(raw.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean));
}

function displayName(modelId) {
  for (const [re, name] of DISPLAY_FAMILY) {
    if (re.test(modelId)) return name;
  }
  return modelId;
}

function shouldSkipGoogle(regionCode, cfCountry) {
  const a = (regionCode || "").trim().toUpperCase();
  const b = (cfCountry || "").trim().toUpperCase();
  return GOOGLE_RESTRICTED_REGIONS.has(a) || GOOGLE_RESTRICTED_REGIONS.has(b);
}

function isRetryableStatus(status) {
  return status === 429 || status === 503;
}

function defaultGeminiModel(env) {
  return (env && env.GEMINI_MODEL && env.GEMINI_MODEL.trim()) || "gemini-3.8-flash";
}

function googleModels(env) {
  if (env && env.GEMINI_MODELS && env.GEMINI_MODELS.trim()) {
    return parseList(env.GEMINI_MODELS, DEFAULTS.google);
  }
  const primary = defaultGeminiModel(env);
  const rest = DEFAULTS.google.filter((id) => id !== primary);
  return [primary, ...rest];
}

/**
 * Build the ordered route list. Providers with no key (or no AI binding) are
 * omitted at call time; this function only decides order and ids.
 */
function buildRoutes(env = {}, { skipGoogle = false } = {}) {
  const on = enabledProviders(env);
  const routes = [];
  // 1. Workers AI gpt-oss first — no Groq key required.
  if (on.has("workersai")) {
    for (const id of parseList(env.CF_GPT_OSS_MODELS, DEFAULTS.workersaiGptOss)) {
      routes.push({ id, provider: "workersai", displayName: displayName(id) });
    }
  }
  // 2. Groq is optional and is omitted later if GROQ_API_KEY is unset.
  if (on.has("groq")) {
    for (const id of parseList(env.GROQ_MODELS, DEFAULTS.groq)) {
      routes.push({ id, provider: "groq", displayName: displayName(id) });
    }
  }
  if (on.has("google") && !skipGoogle) {
    for (const id of googleModels(env)) {
      routes.push({ id, provider: "google", displayName: displayName(id) });
    }
  }
  // Other Workers AI models after Google, before OpenRouter overflow.
  if (on.has("workersai")) {
    for (const id of parseList(env.CF_MODELS, DEFAULTS.workersaiOther)) {
      routes.push({ id, provider: "workersai", displayName: displayName(id) });
    }
  }
  if (on.has("openrouter")) {
    for (const id of parseList(env.OPENROUTER_MODELS, DEFAULTS.openrouter)) {
      routes.push({ id, provider: "openrouter", displayName: displayName(id) });
    }
  }
  if (on.has("zai")) {
    for (const id of parseList(env.ZAI_MODELS, DEFAULTS.zai)) {
      routes.push({ id, provider: "zai", displayName: displayName(id) });
    }
  }
  return routes;
}

function providerReady(provider, env) {
  switch (provider) {
    case "groq": return Boolean(env.GROQ_API_KEY); // optional: skip entirely when unset
    case "google": return Boolean(env.GEMINI_API_KEY);
    case "workersai": return Boolean(env.AI);
    case "openrouter": return Boolean(env.OPENROUTER_API_KEY);
    case "zai": return Boolean(env.ZAI_API_KEY);
    default: return false;
  }
}

/**
 * Try each ready route in order. `call` must return { ok, status, content, error }.
 * 429/503 fall through; other errors also fall through so the user still gets an answer.
 * The last error is returned if the pool is exhausted.
 */
async function completeWithFallback({ env, region, cfCountry, call }) {
  const skipGoogle = shouldSkipGoogle(region, cfCountry);
  const routes = buildRoutes(env, { skipGoogle }).filter((r) => providerReady(r.provider, env));
  if (routes.length === 0) {
    return { ok: false, status: 503, error: "No free-pool providers are configured." };
  }
  let last = { ok: false, status: 503, error: "All free-pool providers failed." };
  for (const route of routes) {
    const result = await call(route, env);
    if (result && result.ok && result.content) {
      return {
        ok: true,
        content: result.content,
        model: route.id,
        modelDisplayName: route.displayName,
        provider: route.provider,
      };
    }
    last = result || last;
    if (result && isRetryableStatus(result.status)) continue;
    // Non-retryable still advances: a missing model should not sink the pool.
    continue;
  }
  return last;
}

function dailyLimit(env) {
  const n = Number.parseInt((env && env.DAILY_LIMIT) || "10", 10);
  return Number.isFinite(n) && n > 0 ? n : 10;
}

function quotaKey(deviceId, now = new Date()) {
  const day = now.toISOString().slice(0, 10); // UTC date
  return `quota:${day}:${deviceId}`;
}

module.exports = {
  GOOGLE_RESTRICTED_REGIONS,
  DEFAULTS,
  displayName,
  shouldSkipGoogle,
  isRetryableStatus,
  defaultGeminiModel,
  googleModels,
  buildRoutes,
  providerReady,
  completeWithFallback,
  dailyLimit,
  quotaKey,
};
