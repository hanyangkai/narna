# NARNA parity roadmap — Hermes & OpenClaw

**Updated:** 2026-08-31 (v0.2.8)  
**Baseline:** [`HERMES-COMPARE.md`](./HERMES-COMPARE.md)

NARNA strategy: **Borrow runtime, own Decision Layer (ADQA).**  
Target: agent that *feels* like Hermes/OpenClaw on social + tools, with DQS moat they lack.

---

## Scorecard (target Q4 2026)

| Area | Hermes | OpenClaw | NARNA now | Target |
|------|--------|----------|-----------|--------|
| Social channels | ~6 gold | 77+ | **15+ registered** | 15 live |
| Tool loop + BYOK | ✅ | ✅ | ✅ | ✅ |
| Browser / computer-use | ✅ | ✅ | ✅ (Playwright) | ✅ |
| Skills (SKILL.md) | ✅ | ✅ | ✅ | ✅ |
| Gateway / pairing | ✅ | ✅ | ✅ | ✅ |
| Multi-agent workspace | ✅ | ✅ | 🟡 | ✅ |
| ADQA / Decision Memory | ❌ | ❌ | ✅ | ✅ **moat** |
| Community / stars | 239k | 388k | 0 | organic |

---

## Phase S — Social everywhere (current)

- [x] Channel registry (`uap/channels/registry.py`)
- [x] X, Facebook, YouTube, Instagram gateways
- [x] Cloud webhooks for X / FB / IG / YouTube
- [x] YouTube comment poll in `gateway run`
- [x] WhatsApp Cloud API (non-Twilio) native
- [x] X long-poll fallback (`UAP_X_POLL=1`)
- [x] TikTok + LinkedIn outbound
- [x] iMessage bridge (BlueBubbles / Beeper)
- [x] LINE, WeChat stubs for APAC

**Verify:** `pytest tests/test_social_channels.py tests/test_channel_expansion.py`

---

## Phase R — Runtime hardening

- [ ] Docker shell socket mount docs + compose fix
- [x] Modal/Daytona + Singularity/Vercel BYOK HTTP backends
- [ ] Notarized .dmg / signed .msi
- [ ] `@narna/client` npm for web embeds
- [x] Multi-tenant gateway pairing isolation (per channel/external)
- [x] Desktop update check (`narna update check`)
- [x] Honcho-lite v2 (PROJECT.md + FTS lessons + KG observe)
- [x] Subagent session isolation
- [x] Desktop Jobs delete + gateway hot-restart

---

## Phase M — Moat (keep ahead of Hermes/OpenClaw)

- [x] Decision Trace / Replay / Benchmark
- [x] ADQA on gateway reply formatters (TG poll + social formatters)
- [x] Auto-lesson write on DQS ≥ 70
- [x] OpenClaw plugin scaffold (`plugins/narna-openclaw`) — publish to npm optional
- [ ] Hermes `delegate_task` → NARNA ADQA sidecar doc

---

## What we will NOT clone

| Item | Why |
|------|-----|
| Nous Portal | BYOK lock |
| OpenClaw 77 channels day-1 | Focus gold paths + webhooks |
| RL / trajectory training | Research, not product |
| Replace LangGraph/CrewAI | Adapter-only |
| Electron/Tauri native shell | Portable + browser desktop |
| Apple/MS notarization | Needs vendor accounts |

---

## Weekly KPI

1. `configuredCount` from `narna gateway channels` on demo VPS  
2. First external GitHub star / fork  
3. First paid Pro via crypto billing E2E  
4. One public demo: same prompt on Telegram + WhatsApp + X with ADQA score visible
