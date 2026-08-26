# NARNA vs Hermes Agent (repo compare)

**Hermes source:** [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)  
**NARNA stance:** Decision-quality agent (ADQA) + Hermes-like runtime surfaces. **BYOK** — user brings LLM keys (no hosted OpenRouter required).

## Product model

| | Hermes | NARNA (aligned) |
|--|--------|-----------------|
| LLM | User `hermes model` / OpenRouter / Portal / Ollama | User key in Ask UI or `/settings/models` |
| Hosted free LLM | Optional Nous Portal sub | **None** — mock without key |
| Moat | Self-improving skills + terminal backends | **ADQA / DQS** + Decision Memory |

## Feature matrix (Hermes README / architecture)

| Area | Hermes | NARNA now | Gap |
|------|--------|-----------|-----|
| Core loop | `run_agent.py` plan→act tools | `narna_agent.ask` tool loop | Smaller tool count |
| BYOK models | First-class | **Yes** (Free+) | — |
| Native `tool_calls` | OpenAI tools schema | **Yes** (+ JSON-fence fallback) | — |
| Tools registry | 40–60+ self-registering | ~20 allowlisted tools | Vision, TTS, image gen, HA |
| Terminal backends | local, Docker, SSH, Modal, Daytona, Vercel, Singularity | local + optional docker | SSH/Modal/Daytona |
| Shell approval | Interactive gates | `UAP_SHELL_REQUIRE_APPROVAL` / `approved=true` | Rich UI pairing |
| Browser | Playwright / Browser Use gateway | navigate/snapshot (fetch±playwright) | Full computer-use |
| Skills | Auto-create + hub + agentskills.io | Auto DQS≥75 + local Skill Hub + **SKILL.md** import/export | Network hub scale |
| Memory | FTS5 + Honcho dialectic | SQLite FTS5 + crude profile notes | Honcho-depth user model |
| Gateway | Persistent process, many platforms | HTTP webhooks: TG/Discord/Slack/WA/Signal/Email | Unified gateway daemon, voice memos |
| Cron | NL cron → any channel | Agent jobs + ticker | NL cron + delivery fan-out |
| Subagents | Parallel + execute_code RPC | delegate + parallel_delegate ≤3 | RPC tool-calling from code |
| CLI / TUI | Full `hermes` TUI | `narna ask` / `narna reason` JSON | Rich TUI |
| Slash cmds | `/new` `/model` `/skills` … | Ask: `/new` `/skills` | Full command set |
| MCP | First-class | MCP tools exist (ADQA/ask) | Broader MCP host |
| Desktop app | Hermes Desktop | PWA only | Native desktop |
| Security | Approval gates, DM pairing | Allowlists + ADQA guardian + shell approval | Interactive approvals UX |
| Research | Trajectory / RL envs | — | Out of scope |
| Tool Gateway (Nous) | Firecrawl/FAL/TTS/Browser Use via Portal | User BYOK tools only | Won't clone paid portal |

## What NARNA will not clone wholesale

- Become a free ChatGPT wrapper (no company-paid LLM for all users)
- 50+ messaging platforms day-one
- RL training environments
- Nous Portal–style hosted Tool Gateway as default

## Shipped this pass (Hermes align)

1. BYOK Free + Ask localStorage key + no hosted OpenRouter fallback  
2. OpenAI-native `tools` / `tool_calls` in Model Router + agent loop  
3. Shell human-approval gate (`UAP_SHELL_REQUIRE_APPROVAL`)  
4. agentskills.io `SKILL.md` import/export (`skill_md` + API)  

## Still highest-value remaining gaps

1. Richer Ask UI for shell approve / slash `/model`  
2. Unified gateway process (vs per-channel HTTP)  
3. Richer TUI  
4. More tools (vision/TTS/image) only if BYOK-backed  

Last updated: 2026-08-26
