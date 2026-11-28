# Nana AI in-app agent skills

Declarative skill registry + planner/executor for multi-step work on free chat
(on-device Foundation Models → free-pool Worker → BYOK).

- **Registry** — `SkillDefinition` + `SkillHandler` (name, description, JSON schema, on-device vs networkFree, permission).
- **Planner** — LLM JSON tool plan when available; heuristic fallback otherwise.
- **Executor** — runs `parallel_group` batches with a concurrency cap; streams `AgentTaskProgress` to the chat UI.
- **Tool calling** — native OpenAI `tool_calls` parse **or** JSON-prompted fallback (`ToolCallParser`).

Skills never require owner-paid APIs. Network skills use official free/keyless endpoints only (Wikipedia, DuckDuckGo Instant Answer, MyMemory) with in-memory cache + rate limits.
