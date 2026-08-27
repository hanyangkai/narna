# Prod Agent Parity 80–90% (Hermes + OpenClaw)

**Goal:** NARNA feels like a market agent on the **production path** (Ask + Desktop + Telegram + Docker shell + Playwright), while staying Decision Quality Infrastructure — not a Hermes/OpenClaw clone.

**Companion:** [`HERMES-COMPARE.md`](./HERMES-COMPARE.md) · [`HERMES-GAP-PLAN.md`](./HERMES-GAP-PLAN.md)

---

## Status legend

| Tag | Meaning |
|-----|---------|
| **Parity** | Works OOTB on the documented prod path |
| **Near** | Shipped; depth or ops defaults still thinner than Hermes/OpenClaw |
| **Stub** | Interface + clear error without BYOK/creds; not battle-tested live |
| **Skip** | Intentionally out of scope |

---

## Hermes vs NARNA (prod path)

| Area | Hermes | NARNA prod target | Status |
|------|--------|-------------------|--------|
| BYOK + tool loop | ✓ | ✓ 44 tools | **Parity** |
| Browser computer-use | Playwright | VPS `INSTALL_BROWSER=1` + `UAP_BROWSER_ENABLED=1` | **Parity** (prod) / Near (dev without Playwright) |
| Terminal sandbox | Docker default | `UAP_SHELL_BACKEND=docker` on VPS | **Near** → **Parity** when socket mounted |
| Modal / Daytona / Singularity / Vercel | Live backends | HTTP stubs + BYOK URL | **Stub** |
| Messaging | 20+ | Telegram · Discord · Slack gold; WhatsApp Twilio; Signal/Email bridge | **Near** |
| Memory | Honcho | FTS5 + MEMORY.md / USER.md | **Near** |
| Skills network | Hub | zip + public index sync | **Near** |
| Desktop | Notarized native | Portable Windows zip + `narna desktop` | **Near** |
| Nous Portal / RL | ✓ | — | **Skip** |

---

## OpenClaw vs NARNA

OpenClaw is an **agent OS** (gateway + ClawHub skills + MCP). NARNA is **not** competing on skill marketplace size.

| Area | OpenClaw | NARNA | Status |
|------|----------|-------|--------|
| MCP client / thousands of skills | Native | Consume via host; expose ADQA + ask | **Integration** |
| MCP server | `openclaw mcp serve` | `https://api.narna.org/mcp` | **Parity** (ADQA surface) |
| Decision quality | — | ADQA · Trace · Replay · Benchmark | **Moat** |
| Runtime tools over MCP | Full agent tools | Honest: evaluate + ask + status — **not** all 44 tools | **Near** |

Install skill: [`plugins/narna-openclaw/SKILL.md`](../plugins/narna-openclaw/SKILL.md)

---

## Channel honesty

| Channel | Mode | Notes |
|---------|------|-------|
| Telegram | `poll` + webhook | Gold path; pairing default on gateway profile |
| Discord | `poll` (channel history) | Requires `UAP_DISCORD_POLL_CHANNELS` |
| Slack | `poll` (conversations.history) | Requires `UAP_SLACK_POLL_CHANNELS` |
| WhatsApp | `webhook` (Twilio) | Env-gated |
| Signal | `stub` | Forward JSON to `UAP_SIGNAL_WEBHOOK_URL` — not signal-cli |
| Email | `webhook` inbound | Ask yes; SMTP reply mainly via job delivery |

---

## Prod checklist

1. Paste BYOK → Ask with real browser tools when enabled  
2. Shell sandboxed (`docker`) on VPS when Docker socket available  
3. Telegram reliable; Discord/Slack usable  
4. OpenClaw/Cursor: MCP `narna_adqa_check` / `narna_agent_ask` / `narna_runtime_status`  
5. Docs never oversell Signal / Email / Modal as full Hermes

Last updated: 2026-08-27
