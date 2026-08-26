# NARNA vs Hermes Agent (repo compare)

**Hermes source:** [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)  
**NARNA stance:** Decision-quality agent (ADQA) + Hermes-like runtime surfaces. **BYOK** — user brings LLM keys (no hosted OpenRouter required).

## Product model

| | Hermes | NARNA (aligned) |
|--|--------|-----------------|
| LLM | User `hermes model` / OpenRouter / Portal / Ollama | User key in Ask UI or `/settings/models` |
| Hosted free LLM | Optional Nous Portal sub | **None** — mock without key |
| Moat | Self-improving skills + terminal backends | **ADQA / DQS** + Decision Memory |

## Feature matrix

| Area | Hermes | NARNA now | Gap |
|------|--------|-----------|-----|
| Core loop | plan→act tools | `narna_agent.ask` | — |
| BYOK models | First-class | **Yes** (Free+) | — |
| Native `tool_calls` | OpenAI tools | **Yes** + JSON fence | — |
| Tools | 40–60+ | **~28** (+ http/image/vision/jobs/profile) | HA, TTS voice notes |
| Terminal | 7 backends | local · docker · **ssh** | Modal/Daytona/Vercel |
| Shell approval | Interactive | env + Ask Approve button | DM pairing |
| Browser | Computer-use | navigate/snapshot | click/type/vision loop |
| Skills | Hub + agentskills.io | Hub + **SKILL.md** | Network scale |
| Memory | FTS5 + Honcho | FTS5 + profile get/set | Dialectic depth |
| Gateway | One process | **`narna gateway`** + HTTP webhooks | Voice memos, more pollers |
| Cron | NL → any channel | **`parse_nl_schedule`** + `/cron` + `schedule_job` | Full fan-out delivery |
| Subagents | Parallel + RPC | delegate ≤3 | Code RPC |
| CLI / TUI | Full TUI | **`narna chat`** REPL | Rich fullscreen TUI |
| Slash cmds | Full set | **/help /new /clear /skills /tools /model /provider /memory /jobs /cron** | — |
| Desktop | Hermes Desktop | PWA | Native app |
| Research | Trajectory / RL | — | Out of scope |

## Shipped this pass

1. Full Ask + CLI slash set  
2. NL cron (`nl_cron` + API `schedule` + tool `schedule_job`)  
3. Unified gateway runner (`narna gateway run|once|status`)  
4. BYOK tools: `http_request`, `image_gen`, `vision_describe`, profile_*, jobs_*  
5. SSH shell backend (`UAP_SHELL_BACKEND=ssh`)  
6. `narna chat` interactive REPL  

## Still thinner than Hermes

- Fullscreen TUI / desktop  
- Modal/Daytona sandboxes  
- Honcho-class user model  
- Nous Portal Tool Gateway (intentionally not cloned)  

Last updated: 2026-08-26
