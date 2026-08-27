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

1. Apple/Microsoft **notarized** .msi / .dmg (portable Windows zip + PyInstaller build shipped)  
2. Live Modal/Daytona credentials in prod (stubs work with BYOK env)  
3. Honcho-depth dialectic memory (MEMORY.md lite is enough for moat path)

## Shipped this pass

- `narna desktop` + portable Windows build (`scripts/build_desktop_exe.ps1`)  
- Public skills index (`skills/public-index.json`)  
- Browser · gateway · 44 tools · Trace/Replay/Benchmark · TUI  

Last updated: 2026-08-27
