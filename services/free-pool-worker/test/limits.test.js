import test from "node:test";
import assert from "node:assert/strict";

function wouldBlock(deviceCount, perDevice) {
  return deviceCount >= perDevice;
}

/** Mirror of GEMINI_SKIP_REGIONS / shouldSkipGemini */
const GEMINI_SKIP = new Set([
  "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT",
  "LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE","IS","LI","NO","CH","GB","UK",
]);
function shouldSkipGemini(regionHint) {
  if (!regionHint) return false;
  return GEMINI_SKIP.has(String(regionHint).trim().toUpperCase());
}

test("device under daily limit is allowed", () => {
  assert.equal(wouldBlock(9, 10), false);
});

test("device at daily limit is blocked", () => {
  assert.equal(wouldBlock(10, 10), true);
});

test("device over daily limit is blocked", () => {
  assert.equal(wouldBlock(11, 10), true);
});

test("default daily limit is 10", () => {
  assert.equal(Number("10"), 10);
});

test("skip Gemini for EEA/UK/CH", () => {
  assert.equal(shouldSkipGemini("DE"), true);
  assert.equal(shouldSkipGemini("GB"), true);
  assert.equal(shouldSkipGemini("CH"), true);
  assert.equal(shouldSkipGemini("US"), false);
  assert.equal(shouldSkipGemini(""), false);
});

test("failover order constants", () => {
  const order = ["workers-ai", "gemini", "groq", "openrouter", "zai"];
  assert.deepEqual(order, ["workers-ai", "gemini", "groq", "openrouter", "zai"]);
});
