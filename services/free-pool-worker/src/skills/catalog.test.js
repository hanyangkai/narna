const { test } = require("node:test");
const assert = require("node:assert/strict");
const {
  listSkills,
  getSkill,
  openAITools,
  jsonToolPrompt,
  parseToolCalls,
} = require("./catalog.js");

test("catalog has at least 12 skills covering the default set", () => {
  const skills = listSkills();
  assert.ok(skills.length >= 12);
  const names = new Set(skills.map((s) => s.name));
  for (const n of [
    "web_lookup", "research", "summarize", "draft_text", "translate",
    "plan_todo", "calculate", "calendar_event", "reminder", "notes",
    "describe_image", "document_qa",
  ]) {
    assert.ok(names.has(n), "missing " + n);
  }
});

test("no skill requires owner-paid keys", () => {
  for (const s of listSkills()) {
    assert.deepEqual(s.keysRequired, []);
    assert.ok(s.location === "onDevice" || s.location === "networkFree");
  }
});

test("openAI tools and json prompt are generated", () => {
  const tools = openAITools();
  assert.equal(tools[0].type, "function");
  assert.ok(jsonToolPrompt().includes("tool_calls"));
  assert.ok(jsonToolPrompt().includes("calculate"));
});

test("parseToolCalls supports JSON fallback and native envelope", () => {
  assert.deepEqual(
    parseToolCalls('{"tool_calls":[{"name":"calculate","arguments":{"expression":"1+2"}}]}'),
    [{ name: "calculate", arguments: { expression: "1+2" } }]
  );
  const plan = parseToolCalls('{"steps":[{"skill":"notes","arguments":{"action":"list"},"parallel_group":1}]}');
  assert.equal(plan[0].name, "notes");
  assert.equal(plan[0].parallel_group, 1);
  const native = parseToolCalls(JSON.stringify({
    choices: [{ message: { tool_calls: [{ function: { name: "summarize", arguments: "{\"text\":\"x\"}" } }] } }],
  }));
  assert.equal(native[0].name, "summarize");
  assert.equal(native[0].arguments.text, "x");
  assert.deepEqual(parseToolCalls("hello"), []);
});

test("getSkill returns null for unknown", () => {
  assert.equal(getSkill("nope"), null);
  assert.equal(getSkill("calculate").location, "onDevice");
});
