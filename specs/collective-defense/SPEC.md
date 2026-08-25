# Collective Threat Signatures — Layer 3 (NGS-0020)

- **Status:** Active (runtime v0)
- **RFC:** [`../../rfcs/ngs/NGS-0020-collective-defense.md`](../../rfcs/ngs/NGS-0020-collective-defense.md)

## Signature object

```json
{
  "signatureId": "sig_…",
  "version": "0.1",
  "patterns": ["spawn_storm"],
  "patternHash": "sha256:…",
  "riskBand": "critical",
  "orgHash": "hmac-sha256:…",
  "createdAt": "…",
  "standard": "NGS-0020"
}
```

MUST NOT include session graphs, prompts, agent names, or secrets.

## Flow

1. Org opt-in (`narna collective opt-in` / `NARNA_COLLECTIVE_OPT_IN=1`)
2. Publish from Threat Engine report → outbox (+ local inbox)
3. Import peer signatures → inbox
4. Match by pattern overlap
5. Apply → capability restrict and/or local kill
