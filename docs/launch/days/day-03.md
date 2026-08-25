# Day 3 — Adapter spotlight (2026-07-23)

**Theme:** NARNA hooks *before* side effects — show enforce-before with real adapter.

## Must ship (pick one backend item)

- [ ] Run `python examples/e2e_mcp.py` — capture deny proof
- [ ] Or run `examples/e2e_openai.py` with `mode=enforce`
- [ ] Screenshot or terminal paste in ship log

## By role

### Backend (45 min)

```bash
pip install -e ".[dev]"
python examples/e2e_mcp.py
python examples/e2e_openai.py
python -m unittest tests.test_adapter_enforce -v
```

Pick the most visual output (deny message > allow).

### DevRel (15 min)

- [ ] Ship log `2026-07-23.md` with terminal output
- [ ] Discussion: **Ship log 2026-07-23 — enforce-before adapters**
- [ ] Link `docs/ADAPTERS-E2E.md`

### Founder (15 min)

**One-liner (draft):**

> Agent called a tool it shouldn't? NARNA adapters evaluate policy *before* LangGraph/OpenAI/MCP side effects — deny or require approval. `mode=enforce` is default.

- [ ] Post one-liner + terminal snippet
- [ ] Tag relevant ecosystems (#MCP #LangGraph #OpenAI — pick 1–2)
- [ ] Comment on 1 adapter-related GitHub issue elsewhere

## Proof block

```bash
python examples/e2e_mcp.py
# expect governance deny for HIPAA-sensitive action
```

## Success metric

- [ ] Deny or enforce proof visible in ship log
- [ ] ADAPTERS-E2E.md linked from Discussion
- [ ] ≥1 external comment on governance thread

## Tomorrow preview

Day 4: Governance Packages — load EU AI Act once, run anywhere.
