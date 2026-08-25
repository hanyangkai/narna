# NARNA — Complete Roadmap (when is “hết”?)

**Date:** 2026-07-31  
**Honesty:** “Xong hết” tuyệt đối (civilizational AI safety) **không có ngày kết thúc**.  
**“Xong hết” sản phẩm** = Decision OS modules + Guardian Defense-in-Depth v1 shippable.

---

## Definition of Done (DoD)

| Tier | Meaning | Target date |
|------|---------|-------------|
| **A — Guardian spine** | L1–L4 policy runtime + Cloud APIs | ✅ **2026-07-30** |
| **B — Decision OS surface** | Connect · Knowledge · Memory · Decision · Governance · Automation · Marketplace (v0) | **2026-08-14** |
| **C — Enterprise harden** | More packs · host container hook · multi-peer federation demo · console UI | **2026-09-15** |
| **D — Scale / society** | True multi-org CTI hub · legal council bindings · OS-level isolation partners | **2026-Q4+** (open-ended) |

**Bạn hỏi “khi nào xong hết” theo mô tả sản phẩm:** → **Tier B = 14 Aug 2026** · **Tier C = 15 Sep 2026**.  
**Tier D** không commit “done” — chỉ giảm rủi ro theo thời gian.

---

## Calendar (from 2026-07-31)

```text
Jul 31 – Aug 7   │ Wave 1  Connect + Knowledge + Memory v0 + wire Decision context
Aug 8  – Aug 14  │ Wave 2  Automation + Marketplace Decision Packages + 3 more packs
                 │         ★ Tier B DONE
Aug 15 – Aug 31  │ Wave 3  Console UI for Decision/Guardian · federation 2-peer demo
Sep 1  – Sep 15  │ Wave 4  Host container adapter (Docker optional) · pack partners
                 │         ★ Tier C DONE
Sep 16 – Dec     │ Wave 5  CTI hub · Reputation network · enterprise pilots (Tier D)
```

---

## Status board

| Module | Status | Wave |
|--------|--------|------|
| Decision Engine | ✅ | — |
| Governance / Packages / GU | ✅ | — |
| Guardian L2–L4 | ✅ v0 | — |
| **Connect** | ✅ Wave 1 v0 | Aug 7 |
| **Knowledge** | ✅ Wave 1 v0 | Aug 7 |
| **Memory** (durable context) | ✅ Wave 1 v0 | Aug 7 |
| **Automation** | ✅ Wave 1/2 stub | Aug 14 |
| **Marketplace** (Decision Packages) | ✅ `dmarket` | Aug 14 |
| Host OS isolation | ✅ Docker runner dry-run + Dockerfile | execute on hosts with Docker | partner runtimes |
| Multi-org CTI | ✅ **CTI Hub** submit/feed/pull/subscribe | live multi-VPS mesh | society-scale |
| Council bindings | ✅ sealed binding + verify on pass | jurisdiction templates | legal counsel |
| Reputation network | ✅ digest export/import | registry attest deep | network effects |

---

## Exit criteria

### Tier B (Aug 14)
- [x] `narna connect list|probe` → `connect catalog|register|probe`
- [x] `narna knowledge upsert|query`
- [x] `narna memory put|get` (project/customer/contract scopes)
- [x] Decision evaluate uses Knowledge + Memory context
- [x] `narna automate run` (email→decision→approval stub)
- [x] Marketplace lists Decision Packages + install local
- [x] Tests green · api.narna.org redeployed *(Wave 1 shipped 2026-07-31)*

**Wave 1 note:** Tier B checklist functionally complete early; Wave 2 industry packs shipped **2026-07-31** (≥6 Decision Packages).

**Wave 2 shipped:** `legal` · `procurement` · `finance` · `hr` · `hospital` · `crypto` Decision Packages.

### Tier C (Sep 15)
- [x] Web console pages for Decision + Guardian status (`/console/decision`, `/console/guardian`)
- [x] 2-node collective push/pull demo script (`scripts/federation_demo.py`)
- [x] Optional Docker Agent Container runner (`narna container docker-run`, `Dockerfile.agent-container`)
- [x] ≥5 industry Decision Packages seeded *(6 packs — Wave 2)*

**Tier C note:** Core exit criteria shipped **2026-07-31** (ahead of Sep 15 lock). Remaining polish: richer console UX, live multi-VPS peer demo.

### Tier D (Q4+ — open-ended)
- [x] CTI Hub relay — `narna cti …` · `POST /v1/guardian/cti/*` (2026-07-31)
- [x] Council legal bindings — seal + verify on quorum pass (`narna binding …`)
- [x] Reputation network digests — export/import peer bands (`narna reputation export|import`)
- [x] CTI mesh sync — `narna cti hubs|sync` · `scripts/cti_mesh_sync.py` (multi-hub push/pull)
- [x] Jurisdiction templates — `eu-gdpr` · `us-enterprise` · `vn-pdpa` (`narna jurisdiction …`)
- [x] Isolation partners — docker + kubernetes plan (`narna isolation …`)
- [x] Partner runtime certs — `narna isolation certify|certs|verify-cert` · NGS-0016-partner-cert (2026-07-31)
- [x] Society CTI demo — `scripts/cti_society_demo.py` (+ console jurisdiction/isolation panels)
- [ ] Live multi-VPS society mesh / counsel-grade jurisdiction packs *(ongoing)*

**Honesty:** Tier D is never “absolute done.” These are shippable primitives that reduce harm over time.

### Guardian Network v1 (Public Safety — citizen edge)

- [x] Specs NGS-0021/0022/0023 · [`GUARDIAN-NETWORK.md`](./GUARDIAN-NETWORK.md) · [`CITIZEN-GUARDIAN.md`](./CITIZEN-GUARDIAN.md)
- [x] AI Gateway + citizen register + Chrome MV3 extension (Phase 1) — [`apps/guardian-extension/`](../apps/guardian-extension/)
- [x] Universal AI Passport badges (Phase 2)
- [x] Approval UX + audit (Phase 3)
- [x] CTI → devices (Phase 4)
- [x] Emergency broadcast (Phase 5)

### ADQA v2 (Decision Quality Infrastructure)

- [x] [`ADQA.md`](./ADQA.md) · NGS-0024 · DQS 10 attributes · Decision Guardian
- [x] `POST /v1/adqa/check` · attached on `/v1/decision/evaluate`
- [x] Website brand + pricing ladder · Decision Quality Console
- [x] Decision Memory + Outcome Learning (NGS-0025) · [`DECISION-INTELLIGENCE.md`](./DECISION-INTELLIGENCE.md)
- [ ] DQS Network learning across orgs *(ongoing)*

---

## Related

- [`ADQA.md`](./ADQA.md) · [`DECISION-INTELLIGENCE.md`](./DECISION-INTELLIGENCE.md) · [`DECISION-OS.md`](./DECISION-OS.md) · [`GUARDIAN.md`](./GUARDIAN.md) · [`STRATEGY.md`](./STRATEGY.md)
