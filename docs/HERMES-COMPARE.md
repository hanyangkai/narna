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
| Tools count | 40–60+ | **44** | Near |
| Terminal backends | 7 | local/docker/ssh/modal/daytona | Near |
| Memory | Honcho | FTS5 + MEMORY.md/USER.md | Near |
| Subagent RPC | ✓ | `execute_code` + delegate ≤3 | Near |
| Fullscreen TUI / Desktop | ✓ | `narna desktop` + `narna tui` + PWA | **Near** |
| Network Skills Hub | ✓ | zip + sync URL + local hub | Near |
| Nous Portal Tool Gateway | ✓ | intentionally no | Skip |
| Trajectory / RL | ✓ | — | Out of scope |

## Still not end-to-end Hermes

1. Native signed .msi / .dmg installer (zip + pip launcher shipped)  
2. Richer Modal/Daytona (stubs + env-gated HTTP; needs real credentials)  
3. Honcho-depth dialectic memory  

## Shipped this pass

- Browser session: click/type/wait/screenshot/vision  
- Job delivery fan-out + optional Telegram voice  
- Gateway poll + pairing (`UAP_GATEWAY_PAIRING`) + compose profile  
- Shell backends: local/docker/ssh/modal/daytona  
- Tool batch ≥40 · Decision Benchmark · `narna tui` · Skills Hub zip/sync

Last updated: 2026-08-26
