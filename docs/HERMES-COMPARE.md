# NARNA vs Hermes Agent (repo compare)

**Hermes source:** [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)  
**NARNA stance:** Decision-quality agent (ADQA) + Hermes-like runtime. **BYOK**. Moat = ADQA, not Portal clone.

## End-to-end parity scorecard

| Area | Hermes | NARNA | Status |
|------|--------|-------|--------|
| BYOK + tool loop + native tool_calls | ✓ | ✓ | **Parity** |
| Slash commands | ✓ | ✓ Ask + `narna chat` | **Parity** |
| Skills + SKILL.md | ✓ | ✓ | **Near** |
| NL cron + channel delivery | ✓ | ✓ `deliverTo` fan-out | **Near** |
| Unified gateway | ✓ | TG poll + Discord/Slack channel poll + voice | **Near** |
| Browser computer-use | click/type/vision | navigate/click/type/wait/screenshot | **Near** (needs Playwright) |
| Tools count | 40–60+ | **43** | Near |
| Terminal backends | 7 | local/docker/ssh/modal/daytona | Near |
| Memory | Honcho | FTS5 + MEMORY.md/USER.md | Near |
| Subagent RPC | ✓ | `execute_code` + delegate ≤3 | Near |
| Fullscreen TUI / Desktop | ✓ | REPL + PWA | Missing |
| Nous Portal Tool Gateway | ✓ | intentionally no | Skip |
| Trajectory / RL | ✓ | — | Out of scope |

## Still not end-to-end Hermes

1. Fullscreen TUI + native desktop  
2. Richer Modal/Daytona (stubs + env-gated HTTP; needs real credentials)  
3. Honcho-depth dialectic memory  
4. Network-scale Skills Hub  
5. Home Assistant / richer multi-channel voice

## Shipped this pass

- Browser session: `browser_click` / `browser_type` / `browser_wait` / `browser_screenshot` / `browser_vision`  
- Job delivery fan-out → telegram/discord/slack/email (+ optional Telegram voice)  
- Gateway Discord + Slack poll + Telegram voice→Whisper BYOK + optional TTS reply  
- NL cron `via telegram:CHAT_ID` → `deliverTo`  
- Shell backends: `local` / `docker` / `ssh` / `modal` / `daytona`  
- Tool batch ≥40 (+ grep, json_query, uuid, hash, env_get, read_url_head, skill md, TTS)

Last updated: 2026-08-26
