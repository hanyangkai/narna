# NARNA Plugin Template

**Never Replace. Always Extend.**

This folder is the starter for community plugins (`narna-slack`, `narna-discord`, …).

## Layout

```text
plugins/
  TEMPLATE/           ← copy me
  narna-slack/        ← example stub
```

## Create a plugin

```bash
cp -r plugins/TEMPLATE plugins/narna-myintegration
# edit narna-plugin.yaml + src/
```

## Manifest (`narna-plugin.yaml`)

```yaml
apiVersion: narna.ai/v1alpha1
kind: Plugin
metadata:
  id: narna-myintegration
  name: My Integration
  version: 0.1.0
spec:
  extends: [agent, tool]
  permissions: [network]
  compatibility: [openai, mcp]
```

## Rules

1. Plugins **MUST NOT** replace host frameworks.  
2. Plugins **SHOULD** emit Evidence / call `wrap` / respect Constitution denies.  
3. Publish to Registry with `narna publish` when ready.  
4. Prefer MIT / Apache-2.0.
