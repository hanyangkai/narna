# Free LLM API sources for Nana AI (commercial iOS)

Research snapshot for routing **zero-cost-to-owner** free chat.  
Checked against provider docs / FreeLLMAPI catalog notes around **24–25 Nov 2026** (Asia/Saigon). Limits and ToS change often — re-verify before shipping.

**Goal:** users chat free; owner pays $0 ongoing (no scrape / unofficial wrappers).

**Primary curated lists / tools reviewed**

| Resource | Role | Link |
| --- | --- | --- |
| [cheahjs/free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources) | Curated free-endpoint list | GitHub |
| [FreeLLMAPI](https://freellmapi.co/) / commercial-use page | Catalog + ToS notes for free tiers | freellmapi.co |
| [LiteLLM](https://github.com/BerriAI/litellm) | Open-source multi-provider router/proxy | GitHub |
| OpenRouter Free Models Router | `openrouter/free` auto-picks a free model | [openrouter.ai](https://openrouter.ai/docs/faq) |
| Cloudflare AI Gateway | Optional gateway in front of Workers AI / others | [developers.cloudflare.com](https://developers.cloudflare.com/ai-gateway/) |

---

## Ranked top 8 (commercial consumer chat, $0 owner cost)

Rank favors: **commercial/production ToS**, **no training on prompts**, **ongoing free quota** (not one-shot trial), **usable RPM/RPD**, **gpt-oss / Gemini / Gemma availability**, card not required.

| Rank | Provider | Highlight models | Free limits (approx.) | Commercial / production ToS | Card required | Trains on free-tier data? | Official link | Notes for Nana |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| **1** | **Cloudflare Workers AI** | **`@cf/openai/gpt-oss-20b`**, **`gpt-oss-120b`**, **`gemma-4-*`**, Llama/Qwen/Mistral catalog | **10,000 Neurons/day** (both Free & Paid plans); text-gen ~**300 RPM** default (varies); resets **00:00 UTC** | **Allowed** under Self-Serve Subscription + per-model license; no non-commercial clause found | **No** (Workers Free) | **No** — CF does not train on Customer Content | [Pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) · [Data](https://developers.cloudflare.com/workers-ai/platform/data-usage/) · [Models](https://developers.cloudflare.com/workers-ai/models/) | **Best fit.** Already aligns with free-pool Worker. Some frontier models need Paid/credits. |
| **2** | **Groq** | **`openai/gpt-oss-120b`**, **`openai/gpt-oss-20b`**, Llama, Qwen | e.g. gpt-oss: **30 RPM**, **1,000 RPD**, **8K TPM**, **200K TPD** (org-level; console is source of truth) | Integration into Customer Application **not prohibited**; **“not for consumer use”** + no resale — **legal review recommended** for public iOS chat | Typically **no** for Free | **No** by default (see Groq “Your data”; confirm current policy) | [Rate limits](https://console.groq.com/docs/rate-limits) · [Your data](https://console.groq.com/docs/data) | Strongest **ongoing** free RPM/RPD among chat-ready hosts. Consumer-use clause is the main risk. |
| **3** | **Google AI Studio / Gemini API (unpaid)** | **Gemini Flash / Flash-Lite / Pro** (SKU names change); Gemma often via other hosts | Free tier is **RPM / RPD / TPM** per model & project (see AI Studio rate-limits UI; commonly low tens of RPM, hundreds–thousands RPD) | API is for **professional/business** use; apps for users in **EEA, Switzerland, UK must use Paid Services** | **No** for unpaid | **Yes** on unpaid — Google may use content to improve products | [Gemini API terms](https://ai.google.dev/gemini-api/terms) · [AI Studio](https://aistudio.google.com/) | Excellent quality. Prefer **paid** Gemini if EU/UK users or if you must avoid training. |
| **4** | **OpenRouter `:free`** | Many `*:free` routes incl. **gpt-oss**, **Gemma**, community hosts; router `openrouter/free` | **20 RPM**; **50 RPD** if &lt;$10 credits ever purchased; **1,000 RPD** after ≥~$10 credits | May **incorporate into products**; no reselling API / competing marketplace; **upstream model ToS also apply** | **No** for free models | **Depends on upstream** provider behind each `:free` route | [Limits](https://openrouter.ai/docs/api_reference/limits) · [FAQ](https://openrouter.ai/docs/faq) · [Pricing](https://openrouter.ai/pricing) | Great **aggregator fallback**, weak as sole pool (50 RPD). Do not treat all `:free` hosts as equal on privacy. |
| **5** | **Cerebras Inference (Free Trial)** | **`gpt-oss-120b`**, `qwen-3.8-27b`, catalog | **One-time $5**, **30 days**; e.g. gpt-oss-120b trial: **5 RPM**, **30K uncached TPM**, **90K total TPM**, **1M TPH/TPD** | License allows apps + end-user display of outputs; pricing marks Developer tier **“not intended for production”** — treat as **bridge only** | **Yes** (verified payment; not charged until PayGo) | Confirm current privacy/DPA; not marketed as “never train” as clearly as CF | [Rate limits](https://inference-docs.cerebras.ai/support/rate-limits) · [Pricing](https://www.cerebras.ai/pricing) | **Not** an ongoing $0 tier. Useful burst capacity while trial lasts. |
| **6** | **SambaNova Cloud (free / preview offers)** | Often Llama / Qwen / DeepSeek-class (catalog changes) | Free-tier RPM/RPD vary by promo; typically modest — check console | Many free/preview offers are **eval-oriented**; **confirm current ToS before production** | Often **no** for free signup | Confirm current data policy | [SambaNova Cloud](https://cloud.sambanova.ai/) | Keep as **optional overflow** only after counsel/ToS check. |
| **7** | **Mistral (Free mode / La Plateforme)** | Mistral Small / Ministral / Pixtral family (names rotate) | Chat “Free mode” ≠ always free **API**; FreeLLMAPI commercial note: **API needs billing activation** | Commercial API use is normal once billed; free chat mode may allow training unless opted out | Phone / billing depending on path | Free mode: **may train** unless opt-out; paid/API policies differ | [Mistral](https://mistral.ai/) · [Console](https://console.mistral.ai/) | **Do not count on $0 API** until you verify a free API SKU. Prefer paid/opt-out for production privacy. |
| **8** | **Hugging Face Inference Providers** | Open models via HF routers (incl. Gemma / gpt-oss when hosted) | **Free accounts: $0 Inference Providers credits** (must buy); **PRO ≈ $2/mo** credits | Model licenses + HF ToS; commercial use of open weights usually OK | Card for paid credits / PRO | Provider-dependent | [Inference Providers](https://huggingface.co/docs/inference-providers) | **Not zero-cost** for a real free pool. List for completeness / tiny PRO budget only. |

### Not in top 8 (flagged)

| Provider | Why excluded from commercial free pool |
| --- | --- |
| **Cohere trial key** | Explicitly **not** for production or commercial use (~20 RPM chat, ~1k calls/mo). |
| **NVIDIA NIM / API Catalog trial** | Trial terms: **no production**; production needs NVIDIA AI Enterprise / paid path. |
| **GitHub Models** | **Retired** (public preview ended ~Jul 2026) — do not plan on it. |
| **AI Horde** | Commercial OK only if you **give back** ≥ compute you take (run workers) — poor fit for a pure iOS client owner. |

---

## Recommended router fallback order (on 429 / quota / 5xx)

Use for Nana free-pool / LiteLLM / OpenRouter-style failover. Prefer **A→B** on **429**, exhausted daily quota, or upstream outage. Skip providers whose ToS you have not cleared for consumer chat.

| Order | Try | Suggested model preference | Fail over when |
| ---: | --- | --- | --- |
| **A** | **Cloudflare Workers AI** | `gpt-oss-20b` (latency) → `gpt-oss-120b` / `gemma-4-*` (quality) | Neuron day cap, model 429, paid-only model error |
| **B** | **Groq** | `openai/gpt-oss-20b` → `openai/gpt-oss-120b` | Org RPM/RPD/TPM 429 (**if** consumer-use ToS accepted) |
| **C** | **Google Gemini unpaid** | Gemini Flash / Flash-Lite | Project rate limit; **skip for EEA/UK/CH users** or if no-training required |
| **D** | **OpenRouter `:free`** | `openrouter/free` or pinned `…:free` gpt-oss/Gemma | 50 RPD (or 1k after $10 credits), upstream 429 |
| **E** | **Cerebras trial** (if active) | `gpt-oss-120b` | Trial exhausted / card missing / 429 |
| **F** | **SambaNova** (ToS-cleared only) | Best available instruct model | Quota / preview denial |
| **G** | **User BYOK / Agent IAP / Ask ChatGPT·Gemini deep links** | N/A | Free pool empty — product UX, not another scrapable free API |

**Implementation tips**

1. Route **server-side** (Cloudflare Worker already in repo) — never embed provider keys in the iOS binary.  
2. Cap per-device / DeviceCheck before burning org quotas.  
3. Treat free tiers as **best-effort**: no SLA; models disappear; multi-account farming usually violates ToS.  
4. LiteLLM / OpenRouter help with A→B failover; still enforce **your** allowlist (exclude Cohere trial, NIM trial, scrapers).

---

## Provider detail sheets (expanded)

### Cloudflare Workers AI — Rank 1
- **Models:** OpenAI **gpt-oss-20b / 120b**, Google **Gemma 4**, Llama 4 Scout, Qwen, Mistral Small, plus embeddings/ASR/TTS.  
- **Limits:** 10k Neurons/day free; excess fails on Workers Free until UTC midnight.  
- **Commercial:** Yes (Self-Serve + model licenses).  
- **Card:** No for free allocation.  
- **Training:** No on Customer Content.  
- **Link:** https://developers.cloudflare.com/workers-ai/

### Groq — Rank 2
- **Models:** **gpt-oss-20b/120b**, Llama, Qwen, Whisper, etc.  
- **Limits:** Per-model Free tab (gpt-oss often 30 RPM / 1k RPD / 8k TPM / 200k TPD).  
- **Commercial:** App integration allowed; **consumer-use disclaimer** — escalate to counsel for Nana App Store distribution.  
- **Card:** Not required for Free (confirm signup).  
- **Training:** Default posture is no training for API customers — re-read current “Your data”.  
- **Link:** https://console.groq.com/

### Google Gemini (AI Studio free) — Rank 3
- **Models:** Gemini family (Flash recommended for free chat).  
- **Limits:** Per-model free RPM/RPD/TPM in AI Studio.  
- **Commercial:** Professional/business; **Paid required** for EEA/CH/UK end users.  
- **Card:** No for unpaid.  
- **Training:** **Yes** on free/unpaid content.  
- **Link:** https://ai.google.dev/

### OpenRouter `:free` — Rank 4
- **Models:** Dynamic `:free` list; includes open-weight **gpt-oss** / **Gemma** when hosts offer them; `openrouter/free` router.  
- **Limits:** 20 RPM; 50 RPD (&lt;$10 lifetime credits) or 1,000 RPD (≥~$10).  
- **Commercial:** Product incorporation OK; no API resale; honor model provider terms.  
- **Card:** No for free routes.  
- **Training:** Upstream-dependent.  
- **Link:** https://openrouter.ai/

### Cerebras — Rank 5 (trial bridge)
- **Models:** **gpt-oss-120b**, Qwen 3.8 27B, shared catalog.  
- **Limits:** $5 / 30 days; low RPM on gpt-oss trial.  
- **Commercial:** API license allows end-user apps; marketing says Developer not for production.  
- **Card:** **Yes**.  
- **Training:** Confirm current policy.  
- **Link:** https://inference-docs.cerebras.ai/

### SambaNova — Rank 6 (caution)
- **Models:** Cloud catalog (Llama/Qwen/etc.).  
- **Limits:** Promo/free console limits.  
- **Commercial:** Verify; often preview language.  
- **Card:** Often no.  
- **Training:** Verify.  
- **Link:** https://cloud.sambanova.ai/

### Mistral — Rank 7 (API likely not free)
- **Models:** Small / Ministral / vision variants.  
- **Limits:** Free **chat** mode ≠ free **API**.  
- **Commercial:** OK when properly subscribed.  
- **Card / phone:** Common.  
- **Training:** Free mode may train unless opt-out.  
- **Link:** https://mistral.ai/

### Hugging Face Inference Providers — Rank 8 (not $0)
- **Models:** Broad open-model catalog.  
- **Limits:** Free user **no** monthly credits; PRO small stipend.  
- **Commercial:** Subject to model + HF terms.  
- **Card:** For credits.  
- **Training:** Provider-dependent.  
- **Link:** https://huggingface.co/docs/inference-providers

---

## EXCLUDED — ToS-violating / unofficial (do not use)

Flag and ban from Nana free-pool, LiteLLM configs, and docs. These reverse-engineer or scrape consumer web UIs / unofficial endpoints.

| Project / pattern | Why banned |
| --- | --- |
| **gpt4free** (`xtekky/gpt4free` and forks) | Scrapes / unofficial access to paid consumer products |
| Unofficial **ChatGPT** / **Claude.ai** / **Gemini web** wrappers, “free ChatGPT API” browser reverse-engines | Violates provider ToS; fragile; App Store / abuse risk |
| Credential-stuffed or shared-cookie “pools” | Account theft / ToS / legal risk |
| Any “unlimited GPT-4 free API” that is not an official provider key | Assume scraper unless proven otherwise |

**Rule:** Only official keys from providers in the top-8 table (or paid BYOK). Prefer Cloudflare → Groq → Gemini → OpenRouter chain above.

---

## Practical recommendation for Nana AI v1.1 free chat

1. **Primary:** Cloudflare Workers AI (`gpt-oss` / Gemma) on the existing free-pool Worker — best ToS + privacy + $0.  
2. **Secondary:** Groq **after** legal OK on consumer-use language.  
3. **Tertiary:** Gemini free only where geo + privacy allow; else skip to OpenRouter `:free`.  
4. **Never:** Cohere trial, NVIDIA trial, GitHub Models, gpt4free/scrapers.  
5. When the free pool is empty: **on-device Foundation Models** (where available) → **BYOK** → **Agent IAP** / Ask ChatGPT·Gemini links.

---

*Document only — no runtime code changes. Re-check official rate-limit and ToS pages before production enablement.*
