# NARNA parity roadmap — Hermes & OpenClaw

**Updated:** 2026-08-31  
**Baseline:** [`HERMES-COMPARE.md`](./HERMES-COMPARE.md)

NARNA strategy: **Borrow runtime, own Decision Layer (ADQA).**  
Target: agent that *feels* like Hermes/OpenClaw on social + tools, with DQS moat they lack.

---

## Scorecard (target Q4 2026)

| Area | Hermes | OpenClaw | NARNA now | Target |
|------|--------|----------|-----------|--------|
| Social channels | ~6 gold | 77+ | **12 registered** (4 live, 4 beta, 4 planned) | 15 live |
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
- [ ] WhatsApp Cloud API (non-Twilio) native
- [ ] X long-poll fallback
- [ ] TikTok + LinkedIn outbound
- [ ] iMessage bridge (BlueBubbles / Beeper)
- [ ] LINE, WeChat stubs for APAC

**Verify:** `pytest tests/test_social_channels.py`

---

## Phase R — Runtime hardening

- [ ] Docker shell socket mount docs + compose fix
- [ ] Modal/Daytona live backends (not stub-only)
- [ ] Notarized .dmg / signed .msi
- [ ] `@narna/client` npm for web embeds
- [ ] Multi-tenant gateway isolation per org

---

## Phase M — Moat (keep ahead of Hermes/OpenClaw)

- [x] Decision Trace / Replay / Benchmark
- [ ] ADQA on every gateway reply (already on Ask path)
- [ ] Auto-lesson write on DQS ≥ 70
- [ ] OpenClaw plugin published to npm
- [ ] Hermes `delegate_task` → NARNA ADQA sidecar doc

---

## What we will NOT clone

| Item | Why |
|------|-----|
| Nous Portal | BYOK lock |
| OpenClaw 77 channels day-1 | Focus gold paths + webhooks |
| RL / trajectory training | Research, not product |
| Replace LangGraph/CrewAI | Adapter-only |

---

## Weekly KPI

1. `configuredCount` from `narna gateway channels` on demo VPS  
2. First external GitHub star / fork  
3. First paid Pro via crypto billing E2E  
4. One public demo: same prompt on Telegram + WhatsApp + X with ADQA score visible
