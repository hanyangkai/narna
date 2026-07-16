# NARNA Manifest Specification (`narna.yaml`)

**Version:** 0.1.0  
**Status:** Draft  
**Strategy:** [`../../docs/BORROW-THE-WAVE.md`](../../docs/BORROW-THE-WAVE.md)  
**Compiles to:** [`../constitution/SPEC.md`](../constitution/SPEC.md)

---

## 1. Purpose

`narna.yaml` is the **developer-facing default metadata** for an autonomous entity — analogous to:

| Ecosystem | Manifest |
|-----------|----------|
| Docker | `Dockerfile` |
| GitHub Actions | `action.yml` |
| Kubernetes | `deployment.yaml` |
| MCP | server manifest |
| **NARNA** | **`narna.yaml`** |

Prompts instruct. Frameworks execute. **`narna.yaml` declares who / may / must.**

Full normative charter remains `constitution.yaml`.  
`narna.yaml` **MUST** be compilable into a Constitution document.

---

## 2. File discovery

Loaders **SHOULD** search, in order:

1. `narna.yaml` / `narna.yml`  
2. `.narna/narna.yaml`  
3. `constitution.yaml` (already a Constitution — pass through)

---

## 3. Short-form shape (informative)

```yaml
apiVersion: narna.ai/v1alpha1
kind: Manifest
metadata:
  name: Research Agent
  owner: did:narna:org:example
identity:
  id: research-agent
  version: 0.1.0
capabilities:
  - web.search
  - github.read
  - reasoning
permissions:
  - name: browser
    mode: allow
  - name: filesystem
    mode: read
  - name: wallet
    mode: deny
policies:
  - human_approval
  - no_money_transfer
trust:
  minimum_score: 0.9
compatibility:
  - openai
  - mcp
  - langgraph
```

---

## 4. Compilation rules

A conformant compiler **MUST** map:

| Manifest field | Constitution field |
|----------------|--------------------|
| `identity.id` | `metadata.entityId` + `spec.identity.id` |
| `metadata.name` | `metadata.name` |
| `metadata.owner` | `metadata.owner` + `spec.identity.owner` |
| `capabilities[]` | `spec.capability.supports` |
| `permissions[]` | `spec.permission.grants` |
| `policies[]` | `spec.policy.rules` (via known policy aliases) |
| `trust.minimum_score` | `spec.trust.minScore` |
| `compatibility[]` | `spec.compatibility` map |

Known policy aliases (v0):

| Alias | Rule effect |
|-------|-------------|
| `human_approval` | `ask` when irreversible |
| `no_money_transfer` | `deny` `wallet.transfer` |
| `no_delete_data` | `deny` `filesystem.delete` |
| `log_every_action` | `require` `action_log` |

---

## 5. Conformance

1. Validate Manifest schema when `kind: Manifest`.  
2. Compile to Constitution and schema-validate the result.  
3. SDK one-liners (`wrap`, `Agent`, `track`) **SHOULD** auto-discover `narna.yaml`.
