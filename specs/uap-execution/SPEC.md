# UAP-Execution Specification

**Version:** 0.1.0  
**Status:** Draft  
**Depends on:** UAP-Core 0.1.0  
**Normative companions:** [`../schemas/tool.schema.json`](../schemas/tool.schema.json), [`../schemas/policy-decision.schema.json`](../schemas/policy-decision.schema.json)

---

## 1. Purpose

UAP-Execution defines the **behavioral contract** of an agent run:

- Run lifecycle / state machine
- Tool boundary & adapters
- Permission gating (parameter-aware)
- Memory adapter contract
- Model adapter boundary (LLM-agnostic)
- Event emission requirements during execution

Developers interact primarily with:

```python
agent.run()
```

The runtime **MUST** handle model routing, permission checks, tool calls, and event emission.

---

## 2. Design goals

1. **LLM-agnostic** — GPT / Claude / Gemini / Llama / Ollama are interchangeable behind a Model Adapter.
2. **Deny-by-default** — no permission ⇒ no tool execution.
3. **Observable** — every material step emits Events.
4. **Effectful actions are gated** — tools with side effects require PolicyDecision + Evidence policy.

---

## 3. Run lifecycle

### 3.1 States

```text
Created → Starting → Running → (AwaitingInput)? → Completing → Completed
                                              ↘ Failing → Failed
                                              ↘ Aborting → Aborted
```

| State | Meaning |
|-------|---------|
| `Created` | Run id allocated, not started |
| `Starting` | Identity/Passport loaded, policy pack resolved |
| `Running` | Understand/Act loop active |
| `AwaitingInput` | Policy `ask` or human confirmation pending |
| `Completing` | Final VAP pass (if enabled) |
| `Completed` | Terminal success |
| `Failing` / `Failed` | Terminal failure |
| `Aborting` / `Aborted` | Cancelled by user/runtime |

### 3.2 Required events

| Transition | Required event |
|------------|----------------|
| enter `Starting` | `AgentStarted` |
| policy check | `PolicyEvaluated` |
| tool request | `ToolCallRequested` |
| tool done | `ToolCallExecuted` |
| success terminal | `Completed` |
| failure terminal | `Failed` |

### 3.3 Normative rules

1. A run **MUST** have a unique `runId`.
2. Terminal states **MUST NOT** accept further tool executions.
3. On `ask`, runtime **MUST** enter `AwaitingInput` and **MUST NOT** execute the gated tool until resolution is recorded.
4. Cancellation **MUST** emit a terminal `Failed` or `Aborted` event with reason.

---

## 4. Understand → Act → Prove (runtime loop)

Informative control loop:

```text
loop:
  Understand  — model proposes next step (intent)
  Authorize   — policy evaluates permission for proposed action
  Act         — tool executes if allowed
  Attach      — evidence attached per Evidence Policy
  Prove       — VAP verify/audit (if VAP enabled)
until terminal condition
```

UAP-Execution **MUST** implement Authorize + Act + Attach.  
Prove **MAY** be delegated to VAP; if VAP is disabled, runtime **SHOULD** still attach evidence.

---

## 5. Tool contract

### 5.1 Tool definition

A Tool **MUST** declare:

| Field | Description |
|-------|-------------|
| `name` | Stable tool id (`provider.action`) |
| `capability` | Capability class |
| `requiredPermissions` | Permission names needed |
| `inputSchema` | JSON Schema for inputs |
| `outputSchema` | JSON Schema for outputs |
| `sideEffect` | `none` \| `local` \| `external` \| `irreversible` |
| `evidencePolicy` | What evidence **MUST** be produced |

### 5.2 Side-effect levels

| Level | Meaning | Extra rules |
|-------|---------|-------------|
| `none` | Pure / read-local cache | Evidence MAY be optional |
| `local` | Mutates local state | Evidence SHOULD include before/after hash |
| `external` | Calls external systems | Evidence MUST include source + timestamp |
| `irreversible` | Money move, send email, delete… | Evidence MUST + Policy `ask` SHOULD |

### 5.3 Tool adapters

Runtime binds tools via **Tool Adapter** interface:

- `validate(input) → ok | error`
- `authorize(ctx, input) → PolicyDecision` (or call Policy engine)
- `execute(ctx, input) → ToolResult`
- `collectEvidence(ctx, result) → Evidence[]`

### 5.4 Normative rules

1. Inputs **MUST** validate against `inputSchema` before authorize.
2. Tools **MUST NOT** execute if any `requiredPermissions` are denied.
3. `ToolCallRequested` **MUST** include input fingerprint (`inputHash`).
4. `ToolCallExecuted` **MUST** include `status`, `durationMs`, `outputHash` (or error).
5. For `sideEffect` ∈ {`external`, `irreversible`}, runtime **MUST** attach at least one Evidence object (see UAP-Evidence).

---

## 6. Permission gating (parameter-aware)

### 6.1 Request object

```text
PermissionRequest =
  permission name
  + parameters (amount, url, path, recipient…)
  + agent identity
  + run context (env, org, trust score)
```

### 6.2 Evaluation order (MUST)

1. Schema-validate parameters  
2. Match PermissionGrant / Policy rules  
3. Apply constraints (`maxAmount`, allowlist domains, path prefixes…)  
4. Consider Trust Score threshold if configured  
5. Emit `PolicyEvaluated`  
6. Enforce decision (`allow` / `deny` / `ask`)

### 6.3 Constraint examples (informative)

```yaml
permissions:
  - name: wallet.transfer
    mode: ask
    constraints:
      maxAmount: "100"
      currency: USDT
      recipientsAllowlist:
        - "0xabc..."
  - name: browser.open
    mode: allow
    constraints:
      domainsAllowlist: ["*.exchange.com"]
```

### 6.4 Normative rules

1. Constraint violations **MUST** yield `deny` (not silent clamp), unless policy explicitly documents clamping.
2. Runtime **MUST** include constraint evaluation details in `PolicyDecision.reasons` when denying.
3. Elevated trust **MUST NOT** bypass an explicit `deny`.

---

## 7. Model adapter (LLM boundary)

### 7.1 Principles

1. Models are **pluggable**. AgentSpec `model` is a preference, not a hard dependency.
2. Runtime **MUST NOT** require a specific vendor for conformance.
3. Model outputs are **intents**, not authorized actions.

### 7.2 Required behavior

- Emit `ModelGenerated` with artifact reference / content hash — **not** mandatory raw prompt storage.
- Map model tool-call proposals → ToolCallRequested after validation.
- On model failure, runtime **MAY** retry with backoff; **MUST** bound retries.

### 7.3 Forbidden

- Treating model text as permission grant.
- Executing side effects without PolicyDecision.

---

## 8. Memory adapter

### 8.1 Interface (conceptual)

- `read(keys|query) → records`
- `write(records) → ack`
- `delete(keys) → ack` (if supported)

### 8.2 Normative rules

1. Memory access **MUST** emit `MemoryRead` / `MemoryWrite` events with hashes of keys touched (not necessarily full payloads).
2. Memory adapters **MUST** respect permissions (e.g. `memory.read`, `memory.write`).
3. Memory **MUST NOT** be used as a covert channel to bypass policy.

---

## 9. Event bus

Runtime **SHOULD** expose an internal Event Bus:

- In-process for single agent
- Optionally externalizable (NATS, Kafka…) without changing event schema

Subscribers **MUST NOT** be able to mutate historical events.

---

## 10. Error model

| Class | Behavior |
|-------|----------|
| `ValidationError` | Fail tool request; no execute |
| `AuthorizationError` | Deny; emit PolicyEvaluated(deny) |
| `ExecutionError` | Tool failed; emit ToolCallExecuted(error) |
| `EvidenceError` | Required evidence missing; fail action for external/irreversible |
| `RuntimeError` | Abort run → Failed |

For `external` / `irreversible` tools, missing required evidence **MUST** be treated as failure of the action, even if the tool “succeeded”.

---

## 11. Developer SDK surface (informative, V0 target)

```python
from uap import Agent

agent = Agent.from_spec("agent.yaml")  # or Agent(name="Trading Agent")
result = agent.run(input="...")
audit = agent.audit(run_id=result.run_id)
passport = agent.passport()
```

CLI (target):

```text
uap init
uap doctor
uap verify
uap passport
uap audit
```

Normative requirement for V0 reference impl: at least `run` + event export.  
`audit` / `passport` / `verify` become normative as V1–V3 land.

---

## 12. Conformance checklist

- [ ] Implements run state machine + required events
- [ ] Validates tool I/O schemas
- [ ] Deny-by-default permission gating with constraints
- [ ] Emits PolicyEvaluated before effectful execute
- [ ] Requires evidence for external/irreversible tools
- [ ] Model adapter does not grant authority
- [ ] Memory access is permissioned + logged

---

## 13. Out of scope

- Concrete sandbox (gVisor, Wasm, OS containers) — implementation choice  
- Network allowlists implementation — policy packs  
- Multi-agent orchestration — V6
