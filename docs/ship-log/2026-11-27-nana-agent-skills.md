# Nana AI built-in skill set (1.1)

Branch: `cursor/agent-skills-registry-32f5` → base `feature/nana-1.1-free-chat-agent-sub`.

## What shipped

- Declarative `SkillRegistry` (name, description, JSON schema, location, permission, handler)
- Planner + executor loop with concurrency cap and per-task UI progress
- JSON-prompted tool use for free-pool models without native tools (heuristic fallback when the model returns prose)
- 12 default skills (on-device or official free/keyless APIs only)
- Info.plist purpose strings for Calendar, Reminders, Photos
- Unit tests (Swift) + Worker skill catalog tests
- **Not deployed.** No new secrets. No merge to `main`.

## Skills

| Skill | Location | Permission | Keys |
|-------|----------|------------|------|
| `web_lookup` | networkFree (Wikipedia REST, DuckDuckGo IA) | none | none |
| `research` | networkFree | none | none |
| `summarize` | onDevice | none | none |
| `draft_text` | onDevice | none | none |
| `translate` | networkFree (MyMemory free API) | none | none |
| `plan_todo` | onDevice | none | none |
| `calculate` | onDevice | none | none |
| `calendar_event` | onDevice (EventKit) | calendars | none |
| `reminder` | onDevice (EventKit) | reminders | none |
| `notes` | onDevice | none | none |
| `describe_image` | onDevice (Vision) | photoLibrary | none |
| `document_qa` | onDevice (PDFKit) | none | none |

Queueing multiple tasks is the executor (numbered lines / “and then” / planner `parallel_group`), not a separate skill.
