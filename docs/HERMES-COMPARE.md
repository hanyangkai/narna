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
| Tools count | 40–60+ | **~32** | Thin |
| Terminal backends | 7 | local/docker/ssh | Thin |
| Memory | Honcho | FTS5 + profile | Thin |
| Subagent RPC | ✓ | delegate ≤3 | Thin |
| Fullscreen TUI / Desktop | ✓ | REPL + PWA | Missing |
| Nous Portal Tool Gateway | ✓ | intentionally no | Skip |
| Trajectory / RL | ✓ | — | Out of scope |

## Still not end-to-end Hermes

1. Fullscreen TUI + native desktop  
2. Modal / Daytona / Vercel sandboxes  
3. Honcho-depth dialectic memory  
4. `execute_code` RPC tool-calling from Python  
5. Home Assistant / richer TTS voice *notes outbound*  
6. Network-scale Skills Hub  

## Shipped this pass

- Browser session: `browser_click` / `browser_type` / `browser_wait` / `browser_screenshot`  
- Job delivery fan-out → telegram/discord/slack/email  
- Gateway Discord + Slack poll + Telegram voice→Whisper BYOK  
- NL cron `via telegram:CHAT_ID` → `deliverTo`  

Last updated: 2026-08-26
