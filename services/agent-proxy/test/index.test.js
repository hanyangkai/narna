import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { handleRequest } from "../src/index.js";
import { agentEnv, samplePayload, signTestJws } from "./helpers.js";

async function jwsUnverified(over = {}) {
  const keyPair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  return signTestJws(samplePayload(over), { key: keyPair.privateKey });
}

describe("HTTP handler", () => {
  it("health is ok and reports models as not configured", async () => {
    const res = await handleRequest(new Request("https://agent.test/health"), agentEnv());
    assert.equal(res.status, 200);
    const body = await res.json();
    assert.equal(body.ok, true);
    assert.equal(body.service, "nana-agent-proxy");
    assert.equal(body.modelsConfigured, false);
  });

  it("rejects missing or unverified JWS", async () => {
    const env = agentEnv();
    const missing = await handleRequest(new Request("https://agent.test/v1/agent", { method: "POST", body: "{}" }), env);
    assert.equal(missing.status, 401);
    const bad = await handleRequest(new Request("https://agent.test/v1/agent", {
      method: "POST",
      headers: { "X-StoreKit-JWS": "not.a.jws" },
      body: "{}",
    }), env);
    assert.equal(bad.status, 401);
  });

  it("returns 503 without a paid model key and does not burn credits", async () => {
    const env = agentEnv({ DEV_ALLOW_UNVERIFIED: "1" });
    const token = await jwsUnverified();
    const res = await handleRequest(new Request("https://agent.test/v1/agent", {
      method: "POST",
      headers: { "content-type": "application/json", "X-StoreKit-JWS": token },
      body: JSON.stringify({ system: "s", messages: [{ role: "user", content: "hi" }] }),
    }), env);
    assert.equal(res.status, 503);
    const body = await res.json();
    assert.equal(body.error, "agent_models_not_configured");
    // after refund, a later reserve should still start at 200
    const { consumeCredits } = await import("../src/credits.js");
    const again = await consumeCredits(env, {
      productId: "nana.agent.basic.monthly",
      originalTransactionId: "orig-1",
      expiresDate: Date.now() + 86400000 * 20,
    }, {});
    assert.equal(again.remaining, 199);
  });

  it("serves a mock upstream and decrements credits", async () => {
    const env = agentEnv({
      DEV_ALLOW_UNVERIFIED: "1",
      OPENAI_API_KEY: "sk-test",
    });
    const origFetch = globalThis.fetch;
    globalThis.fetch = async (url) => {
      if (String(url).includes("api.openai.com")) {
        return new Response(JSON.stringify({
          choices: [{ message: { content: "Agent says hello" } }],
        }), { status: 200, headers: { "content-type": "application/json" } });
      }
      return origFetch(url);
    };
    try {
      const token = await jwsUnverified();
      const res = await handleRequest(new Request("https://agent.test/v1/agent", {
        method: "POST",
        headers: { "content-type": "application/json", "X-StoreKit-JWS": token },
        body: JSON.stringify({ messages: [{ role: "user", content: "hi" }] }),
      }), env);
      assert.equal(res.status, 200);
      const body = await res.json();
      assert.equal(body.content, "Agent says hello");
      assert.equal(body.modelDisplayName, "GPT-4o mini");
      assert.equal(body.creditsRemaining, 199);
    } finally {
      globalThis.fetch = origFetch;
    }
  });
});
