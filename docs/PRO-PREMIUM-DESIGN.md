# Pro Premium Design — Desktop Free, Cloud Pro

**Status:** Design v1 (2026-09-01)  
**Principle:** Desktop agent stays **free forever** (Hermes parity). Pro sells **connectivity, cloud brain, and team** — never cripple local agent.

---

## Problem today

| Issue | Evidence |
|-------|----------|
| Desktop has no license check | `desktop_server.py` — no billing |
| Free cloud is more generous than Pro | `billing.py`: free `agent_turns_hard_cap: None`, cloud hard cap 5k |
| Pro value unclear vs Desktop | User pays $20 but Desktop already does everything locally |
| "Cloud memory sync" promised but not built | `NARNA-MARKET-PLAN.md` gap |

**Fix:** Reframe Pro as **"NARNA Cloud Brain"** — optional layer on top of free Desktop.

---

## Product split (user-facing)

```
┌─────────────────────────────────────────────────────────────┐
│  FREE — Desktop + CLI (local)                               │
│  Full agent · 32 tools · ADQA · Decision Memory · BYOK       │
│  Unlimited · data in ~/.narna · no account required         │
└─────────────────────────────────────────────────────────────┘
                              │
                    optional link (API key)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  PRO $20/mo — NARNA Cloud Brain                             │
│  Sync · backup · always-on · MCP hosted · team · alerts     │
└─────────────────────────────────────────────────────────────┘
```

**Tagline:** *"Agent free on your PC. Pro is your decision brain in the cloud."*

---

## Premium feature matrix

### Tier A — Ship first (reuse existing infra)

| # | Feature | Free | Pro | Why users pay |
|---|---------|------|-----|---------------|
| 1 | **Cloud Memory Backup** | — | ✅ Auto daily | Don't lose lessons if PC dies |
| 2 | **Cross-device sync** | — | ✅ | Phone Ask + Desktop share memory |
| 3 | **Link Desktop** | — | ✅ | Paste `uap_live_…` in Desktop Settings → sync |
| 4 | **Hosted MCP** (`api.narna.org/mcp`) | 100 ADQA/mo | 10k ADQA/mo | Cursor/Claude use NARNA ADQA in IDE |
| 5 | **Cloud recurring jobs** | ❌ | ✅ | "Every morning summarize inbox" without PC on |
| 6 | **Always-on channels** | — | ✅ | Telegram/Discord bot hosted on VPS (no local gateway) |
| 7 | **Decision Replay (cloud)** | Local CLI only | Cloud API + merge memory | Replay with full trace history |
| 8 | **Trace retention** | 7 days ingest | 1 year | Audit trail for compliance |

### Tier B — Next quarter

| # | Feature | Free | Pro |
|---|---------|------|-----|
| 9 | **Private skill hub** | Pull public only | Publish + team share |
| 10 | **ADQA alert webhooks** | — | Slack/email on REJECT |
| 11 | **DQS network import** | Read-only | Full priors import |
| 12 | **Team seats (3+)** | — | Shared org memory |

### Never gate (product lock)

- Local agent, shell, browser, skills (pull)
- Basic ADQA scoring locally
- BYOK on Desktop
- Unlimited local turns
- `narna replay` CLI offline

---

## Desktop ↔ Cloud link (core mechanic)

### UX flow

1. User signs up at `/checkout` or `/signup` → gets `uap_live_…`
2. Desktop **Settings** → new tab **"Cloud Pro"**:
   - Paste API key
   - Button **"Verify & link"** → `GET /v1/auth/me` + `GET /v1/billing/status`
   - Show plan badge: Free / Pro (expires date)
3. If Pro → enable sync toggles:
   - ☑ Backup Decision Memory (daily)
   - ☑ Backup traces
   - ☑ Pull cloud lessons on startup

### API (new endpoints)

```
POST /v1/sync/push          # Desktop → cloud (memory + traces bundle)
GET  /v1/sync/pull          # Cloud → desktop (delta since last sync)
GET  /v1/sync/status        # last sync, plan, quotas
```

**Auth:** `Authorization: Bearer uap_live_…`  
**Gate:** `normalize_plan(org.plan) != "free"` for push/pull (free account can link but sync returns 402 + upgrade CTA).

### Desktop implementation

| File | Change |
|------|--------|
| `desktop_static/index.html` | "Cloud Pro" settings tab |
| `desktop_server.py` | `/v1/desktop/cloud/*` proxy or direct cloud calls |
| New `cloud_sync.py` | Zip `decision-memory/`, `decision-traces/`, upload |

**Minimal v1 sync payload:**

```json
{
  "deviceId": "desktop_abc123",
  "memoryMd": "...",
  "lessons": [...],
  "traces": [{ "traceId": "...", "payload": {...} }],
  "syncedAt": "2026-09-01T12:00:00Z"
}
```

Store under existing `tenant_workspace(org_id)` — no new DB tables for v1 (filesystem).

---

## Billing enforcement (fix inverted caps)

### New quotas (`billing.py`)

| Metric | Free (cloud) | Pro (cloud) | Desktop local |
|--------|--------------|-------------|---------------|
| Agent turns/mo | 50 soft / **200 hard** | 5k soft / **20k hard** | ∞ |
| ADQA checks/mo | 100 hard | 10k hard | ∞ |
| Sync push/mo | 0 | 30 | N/A |
| Recurring jobs | 0 | 10 | ∞ (local) |
| MCP tools/call | 100/mo | 10k/mo | local MCP ∞ |
| Ingest GU/mo | 10k | 5M | N/A |
| Trace retention | 7 days | 365 days | local ∞ |

**Rule:** Cloud free must be **usable but tight**; Desktop must stay **unlimited**.

### Plan check helper (new)

```python
# web/backend/app/plan_features.py

FEATURES = {
    "cloud_sync": {"free": False, "cloud": True, "team": True},
    "recurring_jobs": {"free": False, "cloud": True, "team": True},
    "hosted_channels": {"free": False, "cloud": True, "team": True},
    "mcp_adqa": {"free": 100, "cloud": 10_000, "team": 50_000},
    ...
}

def require_feature(org: Organization, feature: str) -> None:
    ...
```

Use in: sync routes, jobs create, MCP meter, social webhooks.

---

## Desktop UI — Pro upsell (non-annoying)

**Settings → Cloud Pro tab:**

| State | UI |
|-------|-----|
| Not linked | "Link cloud account for backup & sync" + link to `/signup` |
| Linked Free | Show features greyed + "Upgrade Pro $20" → `/checkout` |
| Linked Pro | Green badge, sync toggles, last sync time |

**No modal on launch. No nag in chat.** Only visible in Settings + optional footer link.

---

## Implementation phases

### Phase 1 — Foundation (1 week) ✅ shipped 2026-09-01

- [x] Fix `billing.py` quotas (free cloud tighter, pro higher)
- [x] `plan_features.py` + `require_feature()`
- [x] `GET /v1/sync/status` + push/pull
- [x] Desktop Settings: **Cloud Pro** tab — link API key + plan badge + backup
- [x] Update `/pricing` + `brand.ts` with real Pro value props
- [x] Gate cloud Quality/Critical modes + recurring jobs on Pro

### Phase 2 — Sync MVP (1–2 weeks) 🟡 partial

- [x] `POST /v1/sync/push` + `GET /v1/sync/pull`
- [x] Desktop backup/pull buttons
- [ ] Auto daily backup cron on Desktop
- [ ] Merge lessons into tenant `decision-memory/` on pull (server-side)

### Phase 3 — Always-on (2 weeks)

- [ ] Gate social webhooks: Pro = use shared VPS bots with user's org context
- [ ] Cloud recurring jobs UI in `/ask` or `/console`
- [ ] Email on payment + "link desktop" CTA

### Phase 4 — Team (later)

- [ ] Seat billing ($99/seat)
- [ ] Shared org memory across API keys
- [ ] Team console audit log

---

## Pricing page copy (after design)

**Free**
- Desktop Mac/Windows — full agent, unlimited
- Cloud Ask — 200 turns/mo
- Local MCP tools

**Pro $20/mo**
- Cloud Memory Backup & sync across devices
- Hosted MCP for Cursor / Claude Code
- Always-on Telegram & Discord (no PC needed)
- Recurring agent jobs in cloud
- 20k Ask turns/mo · 1-year trace history

**Team** (soon)
- 3+ seats · shared decision brain · audit log

---

## Success metrics

| Metric | Target (90 days) |
|--------|----------------|
| Desktop downloads | Baseline growth |
| Cloud account signups | 20% of downloaders |
| Desktop ↔ cloud link rate | 30% of signups |
| Free → Pro conversion | 5% of linked accounts |
| Pro churn (30-day) | < 15% |

---

## Open questions

1. **Sync conflict resolution** — last-write-wins vs merge lessons by DQS? → v1: append-only lessons, MEMORY.md LWW.
2. **Offline Pro** — grace period 7 days if subscription lapses? → yes, read-only pull.
3. **Enterprise** — self-host sync on their VPS? → same API, `UAP_TENANT_ROOT` per customer.

---

## Related docs

- [`DESKTOP.md`](./DESKTOP.md) — free local agent
- [`NARNA-MARKET-PLAN.md`](./NARNA-MARKET-PLAN.md) — decision layer moat
- [`billing.py`](../web/backend/app/billing.py) — plan quotas
- [`P0-NEEDS.md`](./P0-NEEDS.md) — crypto + deploy
