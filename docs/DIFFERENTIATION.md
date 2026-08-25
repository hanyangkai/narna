# NARNA Differentiation — Not a clone

**Status:** Lock (2026-07-18)  
**Audience:** website, README, investor/partner FAQ

---

## Closest neighbor

**Agent Passport System (APS)** — [agent-passport.org](https://agent-passport.org) / IETF draft — cryptographic identity, monotonic authority attenuation, signed action receipts, gateway enforcement.

Overlapping *words*: passport, governance, adapters, open protocol.  
**Different product.** Do not copy APS slogans (“agent economy”, “receipts that travel with the action”, IETF-first identity lattice).

---

## NARNA wedge (what to say instead)

| Layer | NARNA | APS (neighbor) |
|-------|-------|----------------|
| Standard | **UGS / NGS** (Identity→Policy→Evidence→Trust + Manifest) | APS IETF identity/delegation draft |
| Unit of charge | **GU** from Execution Units / Governance Sessions | Hosted gateway / SDK |
| Compliance | **Governance Packages** (EU AI Act, HIPAA, GDPR…) as portable YAML + marketplace take-rate | Authority scopes / spend / reputation |
| Proof story | **VAP** — Verify · Audit · Prove + ProofBundle | 3-signature intent→policy→receipt |
| Integration | Wrap frameworks; **enforce-before** host side-effects | Gateway as judge+executor |
| Cloud | Registry, Passport verify, packages, telemetry opt-in | Hosted APS gateway |

**One-liner (canonical):**

> NARNA is the **compliance & trust infrastructure** for Agentic AI — portable **Governance Packages**, **UGS**, and **GU metering**. Others execute agents; NARNA makes fleets **governable and billable**.

**Enterprise one-liner:**

> NARNA is the **Decision Layer for Enterprise AI** — every consequential decision ships with **evidence, risk score, policy check, approval chain, and audit log** (Decision OS).

**Not:** “another agent passport protocol.” · **Not:** “another enterprise ChatGPT.”

---

## What to keep unique on the website

Must appear above the fold or in first scroll:

1. **UGS** named (open standard)  
2. **Governance Package / Marketplace** (compliance in one line)  
3. **Govern Once. Run Anywhere.** (slogan lock)  
4. **GU** pricing story (Runtime free · Trust is the product)  
5. **Decision OS** for enterprise buyers (Decision Packages as industry apps)  
6. Table: OpenAI/Anthropic/LangGraph **execute** · NARNA **governs / decides with proof**

Avoid leading with only “Agent Passport” — that phrase is now crowded. Prefer:

- **UGS Passport** (public page)  
- or **Agent Passport (UGS)** with package + trust score + certification
- **Decision Package** when speaking to compliance / legal / ops buyers

---

## Anti-clone checklist (repo + site)

- [ ] GitHub About ≠ old “UAP runtime” copy  
- [ ] Homepage = https://narna.org  
- [ ] Topics include `agentic-ai`, `ai-governance`, `ugs` — not only `uap`  
- [ ] README shows Packages + GU + `mode=enforce` wrap  
- [ ] Landing mentions Marketplace / UGS before generic passport demo  
- [ ] Specs path `rfcs/ngs/` cited as standard surface  

---

## Legal / brand note

MIT code can be forked. Moat is **network + packages + Cloud verify + naming**:

- Brand **NARNA**, standard **UGS**, engine **VAP**, meter **GU**  
- Keep those four names consistent everywhere (site, README, PyPI, API)
