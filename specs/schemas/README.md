# Schemas

JSON Schema Draft 2020-12 contracts for UAP / VAP objects.

| File | Object |
|------|--------|
| `agent-spec.schema.json` | Declarative agent |
| `identity.schema.json` | Signed birth record |
| `passport.schema.json` | Materialized trust view |
| `event.schema.json` | Append-only event envelope |
| `tool.schema.json` | Tool boundary |
| `evidence.schema.json` | Verifiable evidence |
| `policy-decision.schema.json` | allow / deny / ask |
| `trust-score.schema.json` | Rule-based trust |
| `proof-bundle.schema.json` | Portable proof |

`$id` base: `https://uap.dev/schemas/v0.1/`

Validate examples with any Draft 2020-12 validator (e.g. `check-jsonschema`, `ajv`).
