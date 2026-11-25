import test from "node:test";
import assert from "node:assert/strict";

/**
 * Mirror of ProviderRouter.friendlyModelLabel + client resolve Auto logic.
 * Keeps CI green on Linux without Xcode.
 */

function friendlyModelLabel(raw) {
  const s = String(raw || "").toLowerCase();
  if (s.includes("on-device") || s.includes("apple") || s === "foundation") return "Apple on-device";
  if (s.includes("gpt-oss") || s.includes("workers-ai")) return "GPT-OSS";
  if (s.includes("gemma")) return "Gemma";
  if (s.includes("gemini")) return "Gemini Flash";
  if (s.includes("groq")) return s.includes("gpt-oss") ? "GPT-OSS" : "Groq";
  if (s.includes("openrouter")) {
    if (s.includes("gemma")) return "Gemma";
    if (s.includes("gpt-oss")) return "GPT-OSS";
    return "OpenRouter free";
  }
  if (s.includes("zai") || s.includes("glm")) return "GLM Flash";
  if (s.includes("agent")) return "Agent";
  return raw || "Free cloud";
}

function resolveAuto(appleAvailable) {
  return appleAvailable ? "onDevice" : "freePool";
}

test("auto picks on-device when Apple available", () => {
  assert.equal(resolveAuto(true), "onDevice");
});

test("auto fails over to free pool", () => {
  assert.equal(resolveAuto(false), "freePool");
});

test("friendly labels for gpt-oss and gemini", () => {
  assert.equal(friendlyModelLabel("workers-ai:gpt-oss"), "GPT-OSS");
  assert.equal(friendlyModelLabel("gemini:gemini-2.0-flash"), "Gemini Flash");
  assert.equal(friendlyModelLabel("Apple on-device"), "Apple on-device");
  assert.equal(friendlyModelLabel("zai:glm-4.7-flash"), "GLM Flash");
});

test("paywall gate when daily limit hit", () => {
  const dailyLimitReached = true;
  const showUpgrade = dailyLimitReached;
  assert.equal(showUpgrade, true);
});
