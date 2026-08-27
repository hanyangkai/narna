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
| NL cron + channel delivery | ✓ | ✓ `deliverTo` fan-out | **Near** |
| Unified gateway | ✓ | TG + Discord/Slack poll + voice | **Near** (Signal/Email = bridge/stub) |
| Browser computer-use | click/type/vision | navigate/click/type/wait/screenshot/vision | **Parity** on VPS with Playwright; Near without |
| Tools count | 40–60+ | **44** | Near |
| Terminal backends | 7 | local/docker/ssh + modal/daytona stubs | Near / **Stub** remote |
| Memory | Honcho | FTS5 + MEMORY.md/USER.md | Near |
| Subagent RPC | ✓ | `execute_code` + delegate ≤3 | Near |
| Fullscreen TUI / Desktop | ✓ | `narna desktop` + `narna tui` + PWA | **Near** |
| Network Skills Hub | ✓ | zip + sync URL + local hub | Near |
| MCP for other agents | — | ADQA + ask + runtime status | OpenClaw-ready |
| Nous Portal Tool Gateway | ✓ | intentionally no | **Skip** |
| Trajectory / RL | ✓ | — | **Skip** |

## Still not end-to-end Hermes

1. Apple/Microsoft **notarized** .msi / .dmg (portable Windows zip shipped in v0.2.0)  
2. Live Modal/Daytona/Singularity/Vercel backends (**Stub** — BYOK exec URL only)  
3. Honcho-depth dialectic memory (MEMORY.md lite is enough for moat path)  
4. 20+ messaging platforms (gold paths: Telegram · Discord · Slack)

## Shipped

- `narna desktop` + portable Windows build · public skills index  
- Browser · gateway · 44 tools · Trace/Replay/Benchmark · TUI  
- Prod parity track: Playwright on VPS · Docker shell default · OpenClaw MCP skill  

Last updated: 2026-08-27
