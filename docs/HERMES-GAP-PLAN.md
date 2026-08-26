# Hermes Gap Plan — NARNA Agent

**Goal:** Close remaining Hermes runtime gaps without cloning Nous Portal or RL.  
**Strategy:** [`NARNA-MARKET-PLAN.md`](./NARNA-MARKET-PLAN.md) — **Borrow Runtime, Own Decision Layer**  
**Baseline:** `docs/HERMES-COMPARE.md` · 32 tools · BYOK parity ✓  
**Execute with:** `/do` or agent — one phase per session, verify before next.

---

## Two tracks

| Track | Doc | Focus |
|-------|-----|-------|
| **A — Runtime** | This file (P1–P9) | Hermes parity: tools, browser, TUI, gateway |
| **B — Moat** | `NARNA-MARKET-PLAN.md` (B1–B6) | Decision Trace, Replay, Benchmark, ADQA API |

**Rule:** Every Track A feature must log into Decision Trace (B1) once shipped.

---

## Phase 0 — Discovery (done)

| Source | Use |
|--------|-----|
| `docs/HERMES-COMPARE.md` | Gap scorecard |
| `src/uap/narna_agent.py` | Ask loop, tool rounds |
| `src/uap/agent_tools.py` | Tool registry pattern |
| `src/uap/cli.py` | `chat`, `gateway` REPL |
| `src/uap/agent_memory_fts.py` | Honcho-lite starting point |
| `src/uap/browser_session.py` | Playwright session |
| Hermes README | Terminal backends, execute_code RPC, TUI |

**Allowed patterns (copy, don’t invent):**
- New tools → add to `TOOL_SPECS` + handler in `AgentToolbelt` (see `schedule_job`)
- New shell backend → extend `tool_shell_exec` `UAP_SHELL_BACKEND` switch (see `docker`, `ssh`)
- Gateway channel → extend `UnifiedGateway.poll_once()` (see `_poll_telegram`)
- Job delivery → `job_delivery.deliver_job_result()` + `deliverTo` on jobs

**Anti-patterns:**
- No company-hosted OpenRouter fallback
- No Nous Portal Tool Gateway clone
- No RL / trajectory training envs
- Don’t break ADQA scoring on Ask path

---

## Phase 1 — Playwright + browser vision loop (1–2 days)

**Status:** ✅ Shipped — `browser_vision` tool + Docker `INSTALL_BROWSER=1`

**Why:** Computer-use “near” but fails without Playwright in prod Docker.

### Tasks
1. Add optional Playwright to API Docker image (`web/backend/Dockerfile` or compose profile).
   - `pip install playwright` + `playwright install chromium --with-deps` (or slim + deps doc).
2. Env: `UAP_BROWSER_ENABLED=1`, document in `docs/SELF-HOST.md`.
3. Tool `browser_vision`: screenshot → `vision_describe` on saved PNG path (reuse `_browser_screenshot` + `_vision_describe`).
4. Wire `browser_vision` into agent system prompt as preferred multi-step flow.

### Verify
- [x] `pytest tests/test_agent_rpc.py`
- [ ] Smoke on VPS: Ask uses click/type after navigate (manual or script)
- [x] `len(TOOL_SPECS) >= 33`

---

## Phase 2 — Subagent RPC `execute_code` (2–3 days)

**Status:** ✅ Shipped — `src/uap/agent_rpc.py` + `execute_code` tool

**Why:** Hermes collapses multi-step pipelines into zero-context-cost turns.

### Design (minimal)
- New tool `execute_code`: sandboxed Python snippet with injected `call_tool(name, args) -> dict`.
- Implementation: `src/uap/agent_rpc.py` — thread-local toolbelt ref; `call_tool` delegates to `AgentToolbelt.call`.
- Restrictions: same as `code_exec` (no imports except whitelist: `json`, `math`, `re`) + max 3 nested tool calls + timeout 15s.
- Agent loop unchanged; model calls `execute_code` like any other tool.

### Files
- `src/uap/agent_rpc.py` (new)
- `src/uap/agent_tools.py` — `tool_execute_code`, spec, handler
- `tests/test_agent_rpc.py` (new)

### Verify
- [x] Test: `execute_code` calls `calculator` and returns result
- [x] Test: nested depth budget enforced
- [ ] `narna ask "use execute_code to compute 12*12"`

---

## Phase 2b — Decision Trace (Track B1) — **NEXT**

See [`NARNA-MARKET-PLAN.md`](./NARNA-MARKET-PLAN.md) § B1. Blocks Replay + Benchmark.

---

## Phase 3 — Honcho-lite memory v1 (2–3 days)

**Why:** Hermes `MEMORY.md` / `USER.md` + session summarization.

### Tasks
1. `src/uap/agent_memory_md.py` — read/write `workspace/.uap/MEMORY.md`, `USER.md` (Hermes layout).
2. Extend `AgentMemoryFTS`:
   - After each Ask with DQS≥70, append bullet to MEMORY.md (lesson one-liner).
   - `observe_user_message` also updates USER.md preferences section.
3. Inject MEMORY.md + USER.md into `narna_agent.ask` system context (truncate 2k each).
4. Tool `memory_summarize`: LLM compress last N FTS turns → MEMORY.md section (BYOK).
5. Optional cron: `/cron weekly summarize memory` via existing jobs.

### Verify
- [ ] Roundtrip: Ask → MEMORY.md grows
- [ ] `memory_search` hits + MD files consistent
- [ ] Tests in `tests/test_agent_memory_md.py`

---

## Phase 4 — Terminal backends Modal + Daytona stubs (2 days)

**Why:** Hermes “runs anywhere” story; keep BYOK/env-gated.

### Tasks
1. `UAP_SHELL_BACKEND=modal` — POST to Modal sandbox API if `UAP_MODAL_TOKEN` + `UAP_MODAL_APP` set; else clear error.
2. `UAP_SHELL_BACKEND=daytona` — Daytona workspace exec API stub (same pattern as ssh).
3. Document env vars in `docs/SECRETS.md` + `docs/SELF-HOST.md`.
4. No default cloud keys — opt-in only.

### Verify
- [ ] Without env → `{ok:false, error:...not set}`
- [ ] Unit test mocks HTTP exec response
- [ ] `HERMES-COMPARE.md` terminal row → “local/docker/ssh/modal/daytona”

---

## Phase 5 — Rich TUI `narna tui` (3–4 days)

**Why:** Largest UX gap vs Hermes CLI.

### Stack choice
- **Preferred:** `textual` (fullscreen, panels, slash autocomplete) — add optional dep `narna[tui]`.
- Copy patterns from existing `cmd_chat` slash handling (`src/uap/cli.py`).

### Features (MVP)
- Split pane: transcript + input
- Slash autocomplete: `/help` `/model` `/tools` `/cron` …
- Streaming status line (phase: tools / ADQA)
- Ctrl+C interrupt → partial answer preserved
- `--provider` / model from env or `/model`

### Files
- `src/uap/tui_app.py` (new)
- `src/uap/cli.py` — `narna tui` subcommand
- `pyproject.toml` optional extra `[tui]`

### Verify
- [ ] `narna tui` launches on Windows + Linux
- [ ] Slash `/new` clears session
- [ ] No regression: `narna chat` still works without textual

---

## Phase 6 — Voice + TTS outbound (1–2 days)

**Why:** Hermes voice notes on Telegram; we have inbound Whisper stub only.

### Tasks
1. Tool `text_to_speech` — OpenAI TTS BYOK → save `.uap/audio/out.mp3`.
2. `job_delivery` + gateway: if channel=telegram and `deliverAudio=true`, send voice via `sendVoice` API.
3. Gateway: optional reply-as-voice when user sent voice memo (`UAP_GATEWAY_VOICE_REPLY=1`).

### Verify
- [ ] TTS tool returns path without key → `needsKey`
- [ ] Mock test for telegram sendVoice payload shape

---

## Phase 7 — Tool expansion batch (+8 tools, 2 days)

**Target:** 40 tools (Hermes lower bound).

| Tool | Notes |
|------|--------|
| `grep_workspace` | ripgrep in agent-workspace |
| `json_query` | jq-lite via json.loads path |
| `uuid` | ids helper |
| `hash` | sha256 hex |
| `env_get` | allowlisted env keys only |
| `read_url_head` | HEAD request metadata |
| `skill_export_md` | wrap `skill_md.skill_to_markdown` |
| `skill_import_md` | wrap markdown_to_skill + save |

Copy handler style from `workspace_read` / `skill_save`.

### Verify
- [ ] `len(TOOL_SPECS) >= 40`
- [ ] OpenAI tools schema builds without error

---

## Phase 8 — Gateway hardening + deploy (1 day)

### Tasks
1. Docker Compose service `narna-gateway` running `narna gateway run` alongside api.
2. Health: `GET /v1/agent/gateway/status` proxy or CLI JSON in deploy script smoke.
3. DM pairing stub: `UAP_GATEWAY_PAIRING=1` — unknown telegram chat_id → reply with pairing code stored in tenant profile.
4. Update `scripts/deploy_vps_agent.sh` smoke: tools count, gateway status.

### Verify
- [ ] VPS compose up includes gateway when `TELEGRAM_BOT_TOKEN` set
- [ ] Jobs tick + delivery still pass smoke Ask

---

## Phase 9 — Skills Hub network v0 (optional, 2 days)

- Export/import SKILL.md zip bundle
- `POST /v1/agent/skills/hub/sync` — pull public index from configurable URL (not Nous)
- Auto-publish skill when DQS≥80 + user opt-in

**Skip if time-boxed** — not blocking “runtime e2e”.

---

## Out of scope (explicit)

| Item | Reason |
|------|--------|
| Nous Portal / Tool Gateway | BYOK product lock |
| Hermes Desktop native app | PWA sufficient for MVP |
| Trajectory / RL | Research, not product |
| 50+ messaging platforms | Webhooks cover core 6 |
| Honcho full dialectic SDK | Phase 3 is lite MD + FTS |

---

## Execution order (recommended)

```
P1 Playwright+browser_vision  →  P2 execute_code RPC
        ↓                              ↓
P3 Honcho-lite memory        →  P7 tool batch (+8)
        ↓                              ↓
P4 Modal/Daytona stubs       →  P6 TTS outbound
        ↓                              ↓
P5 Rich TUI                  →  P8 Gateway deploy
```

**First PR slice (today):** Phase 1 + Phase 2 (browser vision + execute_code) — highest Hermes-feel per hour.

---

## Definition of Done — “Hermes runtime e2e”

- [ ] 40+ tools, native tool_calls
- [ ] Browser navigate→click→type→vision path works in Docker
- [ ] execute_code RPC with nested tool calls
- [ ] MEMORY.md / USER.md in every Ask context
- [ ] Cron delivers to 4 channels reliably
- [ ] `narna tui` or equivalent fullscreen CLI
- [ ] Gateway in compose with pairing + voice optional
- [ ] Modal OR Daytona backend stub (opt-in)
- [ ] ADQA unchanged on all paths
- [ ] `docs/HERMES-COMPARE.md` scorecard → mostly **Parity** / **Near**

Last updated: 2026-08-26
