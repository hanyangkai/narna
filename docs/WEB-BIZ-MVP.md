# Web & Business MVP — UAP / VAP

**Status:** Draft  
**Audience:** founders, product, engineering  
**Positioning:** Governance Infrastructure for Agentic AI — **Trust as a Service (TaaS)**  
**Business model:** [`BUSINESS-MODEL.md`](./BUSINESS-MODEL.md) — price by governance assets, not events

---

## 0. Tóm tắt quyết định

| Câu hỏi | Trả lời |
|---------|---------|
| MVP kỹ thuật đạt chưa? | **Có** — SDK + CLI + ProofBundle + VAP (xem `MVP.md`) |
| Đủ để gọi vốn với “marketplace sau”? | **Không** — VC sẽ fail như bạn mô tả |
| Doanh thu Day 1 từ đâu? | **Tầng 2 — Cloud** (hosted audit/logs/history), không phải Marketplace hay Trust Score |
| Go-to-market | **B2D** (developer first), enterprise là *pull* từ production usage |
| KPI năm 1 | Adoption > ARR (GitHub/Docker playbook) |

---

## 1. Đánh giá kiến trúc — cần nâng cấp ở đâu?

Kiến trúc hiện tại **đúng hướng spec** cho reference impl. Để phục vụ **web biz + doanh thu**, cần tách thêm 3 lớp — không phá spec OSS.

### 1.1 Giữ nguyên (đừng đụng)

```text
UAP Spec (OSS)     → contract bất biến, cộng đồng adopt
uap-sdk (OSS)      → pip install, Agent.run(), local-first
VAP (OSS)          → verify offline, ProofBundle portable
```

**Nguyên tắc OpenTelemetry:** telemetry/export có thể cloud, **spec + SDK core** vẫn mở.

### 1.2 Nâng cấp bắt buộc (theo thứ tự ưu tiên)

| # | Nâng cấp | Vì sao | Map doanh thu |
|---|----------|--------|----------------|
| **A** | **UAP Export Protocol** (OTLP-like) | SDK gửi events/evidence lên cloud mà không nhét vendor vào spec | Cloud $19–199 |
| **B** | **Multi-tenant Cloud API** | `POST /v1/runs`, `GET /v1/audit`, API keys | Cloud |
| **C** | **Web Console MVP** | Audit, logs, history, verify bundle — không cần self-host | Cloud |
| **D** | **Passport Verify API** (read-only public) | `GET /v1/passport/{agentId}` + badge embed | Passport $99/yr |
| **E** | **Benchmark pipeline** (opt-in anonymized) | Aggregate model/tool/evidence stats | Data / Enterprise |
| **F** | **Package split** | `uap` (OSS) vs `uap-cloud` (exporter, optional dep) | OSS purity |
| **G** | **Identity verify on load** | Passport/Passport badge có giá trị pháp lý hơn | Passport + Enterprise |
| **H** | **RBAC / org / SSO** | Enterprise on-prem + cloud | $30k–100k/yr |

### 1.3 Không cần tối ưu sớm (tránh over-engineer)

- Event bus NATS/Kafka (in-process đủ cho MVP cloud)
- Wasm/gVisor sandbox (enterprise phase 2)
- Remote marketplace (sau khi có 1k+ developers)
- ML-based Trust Score (rule-based đủ cho spec v0)

### 1.4 Kiến trúc mục tiêu (12 tháng)

```text
                    [ Web Console ]  [ Public Passport ]  [ Benchmark API ]
                              \              |                    /
                               \             |                   /
                         [ Cloud Control Plane — multi-tenant ]
                                    |
                         UAP Export Protocol (HTTPS/gRPC)
                                    |
    Application Agents ── uap-sdk (OSS) ── local runtime ── VAP engine
                                    |
                              Any LLM / Tools
```

**Điểm then chốt:** Cloud là **hosted observability + audit** cho agent runs — giống GitHub Actions logs / OTel Collector backend — **không** phải runtime bắt buộc.

---

## 2. Phản biện chiến lược doanh thu (và chỉnh lại)

### 2.1 Bạn đúng — VC sẽ fail nếu trả lời:

- “Marketplace sau” → fail  
- “Trust Score sau” → fail  
- “5 năm nữa mới kiếm tiền” → fail  

### 2.2 Nhưng 5 tầng AWS vẫn đúng — **thứ tự kích hoạt** khác

| Tầng | Sản phẩm | Thu tiền khi nào | MVP web |
|------|----------|------------------|---------|
| **1** | SDK OSS | Không | docs + GitHub + `pip install` |
| **2** | **Cloud** | **Day 1** | console + billing — **governance assets** (agents, registry), not raw events |
| **3** | Enterprise | Có lead production | sales page + contact |
| **4** | Passport Verified | Có agent public/deploy | verify page + badge |
| **5** | Marketplace | Có supply + demand | sau 6–12 tháng |
| **+** | Benchmark API | Có volume opt-in | enterprise tier add-on |

### 2.3 Định vị: OpenTelemetry for AI Agents

**Nói với developer:**

> Cài SDK → mọi agent run emit chuẩn UAP → audit/verify được → cloud optional.

**Không nói:**

> Nền tảng Trust AI / giải quyết AI an toàn.

OTel không thay app; UAP không thay LangChain — **lớp chuẩn telemetry + proof** cho agent execution.

**Tagline đề xuất:**

```text
UAP — OpenTelemetry for AI Agents.
Understand · Act · Prove.
```

---

## 3. B2D — con đường GitHub

```text
100.000 developers (SDK free)
        ↓
1.000 startups (Cloud paid — không muốn host audit)
        ↓
50 enterprise (on-prem / compliance / SSO)
```

Developer **không cần** sales call để bắt đầu:

```bash
pip install uap
uap init && uap run --input "btc price"
```

Cloud **upsell tự nhiên** khi:

- team > 1 người cần xem audit  
- cần retention > 30 ngày  
- cần share ProofBundle với khách hàng  

---

## 4. Web product MVP — phạm vi 90 ngày

Mục tiêu: **có thể thu $19/tháng từ ngày đầu tiên có user trả tiền**, không cần marketplace.

### 4.1 Trang web (marketing)

| URL | Mục đích |
|-----|----------|
| `/` | Landing — OTel for Agents, 3 bước: Install → Run → Prove |
| `/docs` | Quick start (mirror README + spec links) |
| `/pricing` | Free / Pro $19 / Team $49 / Business $199 |
| `/spec` | Link tới UAP spec repo (credibility) |
| `/passport` | Tra cứu passport công khai (free read, verified = paid) |
| `/enterprise` | On-prem, compliance, contact sales |
| `/login` | Console |

### 4.2 Cloud Console (sản phẩm trả tiền)

| Màn hình | Dữ liệu từ spec |
|----------|-----------------|
| **Dashboard** | run count, trust avg, violations |
| **Runs** | event log (hash chain), filter by agent |
| **Run detail** | timeline: Policy → Tool → Evidence → VAP |
| **Audit** | AuditRecord, violations |
| **Proof** | upload/download ProofBundle, verify button |
| **Passport** | materialized view + refresh |
| **Agents** | AgentSpec, identity, capabilities |
| **API Keys** | export protocol credentials |
| **Billing** | Stripe |

### 4.3 Free vs Paid (governance assets — locked)

| | Developer (free) | Cloud Pro $19/mo | Cloud Team $49/mo |
|--|------------------|------------------|-------------------|
| SDK / local runtime | Unlimited | Same | Same |
| Account required | No | Yes | Yes |
| Governed agents | Local unlimited | 20 | 100 |
| Governance packages | Local | Included | 100 |
| Registry | Community (read) | Private | Shared org |
| Passport + verification | Local only | Cloud | Cloud |
| History retention | Local | 90 days | 365 days |
| RBAC / org | — | — | Yes |

**Passport Verified** + **Certification** + **Marketplace (20% take)** — see [`BUSINESS-MODEL.md`](./BUSINESS-MODEL.md).

Legacy cloud APIs may still meter `events/mo` during migration; public pricing uses agent/package limits.

---

## 5. UAP Export Protocol (đề xuất spec phụ — cho Cloud)

Tách khỏi core spec, giống OTLP:

```yaml
# uap export (informative)
POST /v1/ingest/events
Authorization: Bearer uap_live_xxx

body:
  agentId: ...
  runId: ...
  events: [ ... ]      # hash-chained slice
  evidence: [ ... ]    # metadata + uri or inline < 256KB
  proofBundle: ...     # optional, end of run
```

SDK:

```python
# optional: pip install uap-cloud
from uap_cloud import CloudExporter

agent = Agent.from_spec("agent.yaml", exporters=[CloudExporter(api_key="...")])
```

**OSS không phụ thuộc cloud** — exporter là plugin.

---

## 6. KPI năm 1 (CEO dashboard)

**Không đặt ARR là KPI chính tháng 1–6.**

| KPI | Mục tiêu 12 tháng |
|-----|-------------------|
| GitHub stars | 10.000 |
| `pip install uap` / monthly | 50.000 downloads |
| Developers tích hợp (survey / analytics) | 1.000 |
| Startups production (self-report + cloud signup) | 100 |
| Cloud paid subscribers | 200 |
| MRR | $10k+ (200 × ~$50 blended) |
| Enterprise pipeline | 10 qualified |
| Spec contributors (non-team) | 20 |

**Doanh thu Day 1 thực tế:** 1 developer trả $19 vì không muốn host audit → đủ chứng minh *có revenue model*, không cần $1M ARR.

---

## 7. Network loop (moat dài hạn)

```text
Developer cài SDK (free)
    → emit events chuẩn UAP
    → Passport + Trust (derived)
    → publish agent (marketplace, phase sau)
    → company tin evidence, không tin prompt
    → dùng + rating
    → trust tăng
    → developer khác adopt spec
```

**Moat không phải model.** Moat là:

1. **Spec được adopt** (như OTel)  
2. **Execution history** tích lũy trên network  
3. **Verify interop** — ProofBundle verify được mọi nơi  

OpenAI/Anthropic tích hợp vì **enterprise khách hàng yêu cầu audit trail chuẩn** — không vì thích.

---

## 8. Pitch VC (phiên bản không fail)

**Không nói:** “Chúng tôi bán marketplace / trust score.”

**Nói:**

> Chúng tôi xây **OpenTelemetry for AI Agents** — spec mở + SDK miễn phí.  
> Monetize **hosted audit & compliance** ($19–199/mo) từ developer không muốn self-host.  
> Enterprise on-prem $30k+/yr cho ngân hàng/chính phủ.  
> **Đã có revenue** từ cloud beta (target week 8).  
> KPI năm 1: adoption, không phải unicorn ARR.

---

## 9. Roadmap web biz × kỹ thuật

| Tuần | Web / Biz | Engineering |
|------|-----------|-------------|
| 1–2 | Landing + docs + pricing + waitlist | Export protocol draft |
| 3–4 | Login + API keys (Stripe checkout) | `uap-cloud` exporter |
| 5–8 | Console: Runs + Run detail | Ingest API + Postgres |
| 9–10 | Audit + Proof verify UI | Retention + billing meters |
| 11–12 | Passport public lookup | Passport verify flow |
| 13+ | Enterprise page + demos | RBAC, SSO sketch |

---

## 10. Những gì KHÔNG làm trong web MVP

- Marketplace UI (chưa có supply)  
- Trust Score leaderboard (gaming risk)  
- “Chat with your agent” IDE  
- Full LangChain replacement narrative  
- Đổi spec để lock-in cloud  

---

## 11. Liên kết spec hiện có → web

| Spec object | Web surface |
|-------------|-------------|
| `AgentSpec` | Agents page |
| `Identity` | Agent birth certificate |
| `Event` | Run timeline |
| `Evidence` | Evidence viewer + hash |
| `PolicyDecision` | Permission audit |
| `ProofBundle` | Verify / export |
| `Passport` | Public profile |
| `TrustScore` | Dashboard metric (derived, not sold standalone) |

---

## 12. Kết luận

| | |
|--|--|
| **Kiến trúc** | Đủ MVP OSS; cần thêm **Export Protocol + Cloud plane** — không rewrite core |
| **Biz** | Day 1 = **Cloud audit hosting**; Passport/Enterprise/Marketplace đúng thứ tự |
| **Positioning** | **OpenTelemetry for AI Agents** > Trust Platform |
| **Web MVP** | Landing + Pricing + Console (Runs/Audit/Proof) + Stripe |
| **Đạt MVP?** | **Tech: yes.** **Biz: cần ship cloud console để MVP hoàn chỉnh go-to-market** |

Bước tiếp theo đề xuất: **spec `UAP-Export` + scaffold `web/` (landing + console API)**.
