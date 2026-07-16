# @narna/sdk (TypeScript)

Reference TypeScript stub for the NARNA Constitution Layer.

> Specs in `/specs` are the source of truth. This package is a thin client — not a runtime replacement.

```bash
cd sdks/typescript
npm install
npm run build
```

```ts
import { compileManifest, badgeForLevel } from "@narna/sdk";

const constitution = compileManifest({
  apiVersion: "narna.ai/v1alpha1",
  kind: "Manifest",
  identity: { id: "research-agent" },
  capabilities: ["web.search"],
  trust: { minimum_score: 0.9 },
});
```

See also: Python `pip install narna`, [`docs/BORROW-THE-WAVE.md`](../../docs/BORROW-THE-WAVE.md).
