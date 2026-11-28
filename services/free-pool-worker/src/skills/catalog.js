// Declarative skill catalog mirrored from the iOS SkillRegistry.
// The Worker does not execute these skills (they run on-device or via free
// keyless APIs from the app). This file documents the contract for prompts,
// ops, and unit tests — no secrets, no paid APIs.

const SKILLS = [
  {
    name: "web_lookup",
    description: "Wikipedia REST + DuckDuckGo Instant Answer (official free APIs).",
    location: "networkFree",
    permission: "none",
    keysRequired: [],
    parameters: { query: "string", source: "auto|wikipedia|duckduckgo" },
  },
  {
    name: "research",
    description: "Web lookup then digest.",
    location: "networkFree",
    permission: "none",
    keysRequired: [],
    parameters: { topic: "string" },
  },
  {
    name: "summarize",
    description: "On-device extractive summary.",
    location: "onDevice",
    permission: "none",
    keysRequired: [],
    parameters: { text: "string", max_sentences: "number?" },
  },
  {
    name: "draft_text",
    description: "Draft email/message from a brief.",
    location: "onDevice",
    permission: "none",
    keysRequired: [],
    parameters: { brief: "string", style: "email|message|formal|casual", recipient: "string?" },
  },
  {
    name: "translate",
    description: "MyMemory Translation API (keyless free tier).",
    location: "networkFree",
    permission: "none",
    keysRequired: [],
    parameters: { text: "string", langpair: "string" },
  },
  {
    name: "plan_todo",
    description: "On-device to-do / plan list.",
    location: "onDevice",
    permission: "none",
    keysRequired: [],
    parameters: { action: "list|add|add_many|complete|clear_done" },
  },
  {
    name: "calculate",
    description: "Safe on-device arithmetic.",
    location: "onDevice",
    permission: "none",
    keysRequired: [],
    parameters: { expression: "string" },
  },
  {
    name: "calendar_event",
    description: "EventKit calendar create/list.",
    location: "onDevice",
    permission: "calendars",
    keysRequired: [],
    parameters: { action: "create|list", title: "string?", start: "ISO8601?", end: "ISO8601?" },
  },
  {
    name: "reminder",
    description: "EventKit reminders create/list.",
    location: "onDevice",
    permission: "reminders",
    keysRequired: [],
    parameters: { action: "create|list", title: "string?", due: "ISO8601?" },
  },
  {
    name: "notes",
    description: "Private on-device notes.",
    location: "onDevice",
    permission: "none",
    keysRequired: [],
    parameters: { action: "list|save|get|delete" },
  },
  {
    name: "describe_image",
    description: "Vision classification + OCR.",
    location: "onDevice",
    permission: "photoLibrary",
    keysRequired: [],
    parameters: { file_path: "string?", base64: "string?" },
  },
  {
    name: "document_qa",
    description: "PDFKit / text Q&A on device.",
    location: "onDevice",
    permission: "none",
    keysRequired: [],
    parameters: { question: "string", file_path: "string?", raw_text: "string?" },
  },
];

function listSkills() {
  return SKILLS.slice();
}

function getSkill(name) {
  return SKILLS.find((s) => s.name === name) || null;
}

function openAITools() {
  return SKILLS.map((s) => ({
    type: "function",
    function: {
      name: s.name,
      description: s.description,
      parameters: {
        type: "object",
        properties: Object.fromEntries(
          Object.entries(s.parameters).map(([k, v]) => [k, { type: "string", description: String(v) }])
        ),
      },
    },
  }));
}

/** JSON-tool-use system addendum for models without native function calling. */
function jsonToolPrompt() {
  return [
    "You can call tools by replying with ONLY minified JSON:",
    '{"tool_calls":[{"name":"skill_name","arguments":{…}}]}',
    "or",
    '{"steps":[{"skill":"skill_name","arguments":{…},"parallel_group":0}]}',
    "Available tools: " + JSON.stringify(openAITools()),
  ].join("\n");
}

/**
 * Parse model output into tool invocations. Supports native tool_calls envelopes
 * and JSON-prompted fallbacks.
 */
function parseToolCalls(text) {
  if (!text || typeof text !== "string") return [];
  let s = text.trim();
  if (s.startsWith("```")) {
    s = s.replace(/^```(?:json)?/i, "").replace(/```$/, "").trim();
  }
  let obj;
  try {
    obj = JSON.parse(s);
  } catch {
    const start = s.indexOf("{");
    const end = s.lastIndexOf("}");
    if (start < 0 || end <= start) return [];
    try {
      obj = JSON.parse(s.slice(start, end + 1));
    } catch {
      return [];
    }
  }
  if (obj.choices && obj.choices[0] && obj.choices[0].message) {
    obj = obj.choices[0].message;
  }
  if (Array.isArray(obj.tool_calls)) {
    return obj.tool_calls.map((c) => {
      const fn = c.function || c;
      let args = fn.arguments || {};
      if (typeof args === "string") {
        try { args = JSON.parse(args); } catch { args = {}; }
      }
      return { name: fn.name, arguments: args || {} };
    }).filter((c) => c.name);
  }
  if (Array.isArray(obj.steps)) {
    return obj.steps.map((st) => ({
      name: st.skill || st.name,
      arguments: st.arguments || st.parameters || {},
      parallel_group: st.parallel_group || 0,
    })).filter((c) => c.name);
  }
  if (obj.name && (obj.arguments || obj.parameters)) {
    return [{ name: obj.name, arguments: obj.arguments || obj.parameters || {} }];
  }
  return [];
}

module.exports = {
  SKILLS,
  listSkills,
  getSkill,
  openAITools,
  jsonToolPrompt,
  parseToolCalls,
};
