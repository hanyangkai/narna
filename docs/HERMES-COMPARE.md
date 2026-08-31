# NARNA vs Hermes Agent (repo compare)

**Hermes source:** [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)  
**NARNA stance:** Decision-quality agent (ADQA) + Hermes-like runtime. **BYOK**. Moat = ADQA, not Portal clone.  
**Prod plan:** [`PROD-AGENT-PARITY.md`](./PROD-AGENT-PARITY.md) · OpenClaw = integration target, not runtime clone.

## End-to-end parity scorecard

| Area | Hermes | NARNA | Status |
|------|--------|-------|--------|
| BYOK + tool loop + native tool_calls | ✓ | ✓ | **Parity** |
| Slash commands | ✓ | ✓ Ask + `narna chat` | **Parity** |
| Skills + SKILL.md | ✓ | ✓ | **Near** |
| NL cron + channel delivery | ✓ | ✓ Jobs ticker + `deliverTo` | **Near → Parity** (desktop) |
| Unified gateway | ✓ | 15+ channels (LINE/WeChat/iMessage + X poll) | **Near** |
| Browser computer-use | click/type/vision | + one-click `narna browser setup` | **Parity** when Playwright installed |
| Tools count | 40–60+ | **44** | Near |
| Terminal backends | 7 | local/docker/ssh + modal/daytona/singularity/vercel BYOK | **Near** |
| Memory | Honcho | FTS5 + MEMORY/USER/PROJECT.md + KG observe + FTS lessons | **Near** |
| Subagent RPC | ✓ | `execute_code` + delegate ≤3 + isolated `sub_*` sessions | **Near** |
| Fullscreen TUI / Desktop | ✓ | desktop + daemon + Jobs delete + gateway restart | **Near** |
| Network Skills Hub | ✓ | zip + sync URL + local hub | Near |
| MCP for other agents | — | ADQA + ask + runtime status | OpenClaw-ready |
| Nous Portal Tool Gateway | ✓ | intentionally no | **Skip** |
| Trajectory / RL | ✓ | — | **Skip** |

## Still not end-to-end Hermes

1. Apple/Microsoft **notarized** .msi / .dmg  
2. Live Modal/Daytona/Singularity/Vercel against real vendor APIs (BYOK URL ready)  
3. Full Honcho dialectic SDK  
4. Native Electron/Tauri shell  
5. Channels live without user tokens (code ready; ops needs tokens)

**Estimate:** ~90% Hermes runtime feel on desktop path (v0.2.8).

Last updated: 2026-08-31
