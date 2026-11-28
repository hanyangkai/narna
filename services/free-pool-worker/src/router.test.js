const { test } = require("node:test");
const assert = require("node:assert/strict");
const {
  shouldSkipGoogle,
  isRetryableStatus,
  defaultGeminiModel,
  buildRoutes,
  completeWithFallback,
  dailyLimit,
  quotaKey,
  displayName,
  providerReady,
} = require("./router.js");

test("default Gemini model is configurable gemini-3.5-flash-lite, not 2.5", () => {
  assert.equal(defaultGeminiModel({}), "gemini-3.5-flash-lite");
  assert.equal(defaultGeminiModel({ GEMINI_MODEL: "gemini-3.8-flash-lite" }), "gemini-3.8-flash-lite");
  const ids = buildRoutes({}).map((r) => r.id);
  assert.ok(ids.includes("gemini-3.5-flash-lite"));
  assert.ok(!ids.includes("gemini-2.5-flash"));
});

test("order starts with Workers AI gpt-oss, then optional Groq", () => {
  const routes = buildRoutes({});
  assert.deepEqual(routes.slice(0, 2).map((r) => r.id), [
    "@cf/openai/gpt-oss-120b",
    "@cf/openai/gpt-oss-20b",
  ]);
  const providers = routes.map((r) => r.provider);
  const first = (p) => providers.indexOf(p);
  assert.equal(first("workersai"), 0);
  assert.ok(first("workersai") < first("groq"));
  assert.ok(first("groq") < first("google"));
  const llama = routes.findIndex((r) => r.id.includes("llama"));
  assert.ok(first("google") < llama);
  assert.ok(llama < first("openrouter"));
  assert.ok(first("openrouter") < first("zai"));
  assert.equal(providers.at(-1), "zai");
});

test("Groq is skipped when GROQ_API_KEY is unset", () => {
  assert.equal(providerReady("groq", {}), false);
  assert.equal(providerReady("groq", { GROQ_API_KEY: "" }), false);
  assert.equal(providerReady("groq", { GROQ_API_KEY: "gsk_test" }), true);
  assert.equal(providerReady("workersai", { AI: {} }), true);
  assert.equal(providerReady("workersai", {}), false);
});

test("skips Google routes for EEA, UK and Switzerland", () => {
  assert.equal(shouldSkipGoogle("DE"), true);
  assert.equal(shouldSkipGoogle("GB"), true);
  assert.equal(shouldSkipGoogle(null, "CH"), true);
  assert.equal(shouldSkipGoogle("US"), false);
  assert.equal(shouldSkipGoogle("SG"), false);
  const eea = buildRoutes({}, { skipGoogle: true });
  assert.ok(eea.every((r) => r.provider !== "google"));
  assert.equal(eea[0].provider, "workersai");
  assert.equal(eea[0].id, "@cf/openai/gpt-oss-120b");
  assert.ok(eea.some((r) => r.provider === "groq")); // listed, but skipped at call time without a key
});

test("ENABLED_PROVIDERS and model lists are configurable", () => {
  const only = buildRoutes({ ENABLED_PROVIDERS: "zai", ZAI_MODELS: "glm-4.7-flash,glm-4.5-flash" });
  assert.deepEqual(only.map((r) => r.id), ["glm-4.7-flash", "glm-4.5-flash"]);
});

test("429 and 503 are retryable", () => {
  assert.equal(isRetryableStatus(429), true);
  assert.equal(isRetryableStatus(503), true);
  assert.equal(isRetryableStatus(500), false);
  assert.equal(isRetryableStatus(400), false);
});

test("display names", () => {
  assert.equal(displayName("openai/gpt-oss-120b"), "GPT-OSS");
  assert.equal(displayName("gemini-3.8-flash"), "Gemini Flash");
  assert.equal(displayName("google/gemma-4-31b-it:free"), "Gemma");
  assert.equal(displayName("glm-4.7-flash"), "GLM");
});

test("completeWithFallback uses Workers AI gpt-oss first and skips Groq without a key", async () => {
  const env = { GEMINI_API_KEY: "x", AI: {} }; // no GROQ_API_KEY
  const seen = [];
  const result = await completeWithFallback({
    env,
    region: "SG",
    call: async (route) => {
      seen.push(route.provider + ":" + route.id);
      if (route.id === "@cf/openai/gpt-oss-120b") return { ok: false, status: 429, error: "rate limit" };
      if (route.id === "@cf/openai/gpt-oss-20b") return { ok: false, status: 503, error: "high demand" };
      if (route.id === "gemini-3.5-flash-lite") return { ok: true, content: "hello from flash" };
      return { ok: false, status: 500, error: "no" };
    },
  });
  assert.equal(result.ok, true);
  assert.equal(result.content, "hello from flash");
  assert.equal(result.modelDisplayName, "Gemini Flash");
  assert.deepEqual(seen.slice(0, 3), [
    "workersai:@cf/openai/gpt-oss-120b",
    "workersai:@cf/openai/gpt-oss-20b",
    "google:gemini-3.5-flash-lite",
  ]);
  assert.ok(seen.every((s) => !s.startsWith("groq:")));
});

test("completeWithFallback skips Google in DE and uses other Workers AI models", async () => {
  const env = { GEMINI_API_KEY: "x", AI: {} }; // no Groq key
  const seen = [];
  const result = await completeWithFallback({
    env,
    region: "DE",
    call: async (route) => {
      seen.push(route.provider + ":" + route.id);
      if (route.id.startsWith("@cf/openai/gpt-oss")) return { ok: false, status: 429, error: "rate limit" };
      if (route.id.includes("llama")) return { ok: true, content: "llama" };
      return { ok: false, status: 500, error: "no" };
    },
  });
  assert.equal(result.ok, true);
  assert.equal(result.modelDisplayName, "Llama");
  assert.ok(seen.every((s) => !s.startsWith("google:")));
  assert.ok(seen.every((s) => !s.startsWith("groq:")));
  assert.ok(seen.some((s) => s.startsWith("workersai:")));
});

test("daily cap helpers", () => {
  assert.equal(dailyLimit({}), 100);
  assert.equal(dailyLimit({ DAILY_LIMIT: "100" }), 100);
  assert.equal(dailyLimit({ DAILY_LIMIT: "50" }), 50);
  assert.equal(quotaKey("device-1", new Date("2026-11-25T16:00:00Z")), "quota:2026-11-25:device-1");
});

test("circuit breaker skips open routes and reports failures", async () => {
  const failures = [];
  const tried = [];
  const result = await completeWithFallback({
    env: { AI: {}, GEMINI_API_KEY: "x" },
    region: "US",
    cfCountry: "US",
    isOpen: (route) => route.id === "@cf/openai/gpt-oss-120b",
    onFailure: async (route) => { failures.push(route.id); },
    call: async (route) => {
      tried.push(route.id);
      if (route.id === "@cf/openai/gpt-oss-20b") return { ok: false, status: 503, error: "down" };
      return { ok: true, content: "hi" };
    },
  });
  assert.equal(result.ok, true);
  assert.ok(!tried.includes("@cf/openai/gpt-oss-120b"));
  assert.deepEqual(failures, ["@cf/openai/gpt-oss-20b"]);
});

test("when every route is open the breaker is ignored", async () => {
  const result = await completeWithFallback({
    env: { AI: {} },
    region: "DE",
    cfCountry: "DE",
    isOpen: () => true,
    call: async () => ({ ok: true, content: "ok" }),
  });
  assert.equal(result.ok, true);
});
