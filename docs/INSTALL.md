# Install NARNA

## PyPI (recommended)

```bash
pip install narna
narna doctor
```

## From source

```bash
git clone https://github.com/hanyangkai/narna.git
cd narna
pip install -e .
narna doctor
```

## Hello governance (enforce mode)

```python
from narna import wrap

# Enforce before host side-effects (default). Use mode="observe" to migrate.
agent = wrap(my_langgraph_app, vap=True, mode="enforce")
agent.run("summarize quarterly report")
```

Set production default:

```bash
export NARNA_ADAPTER_MODE=enforce
```

## Adapter e2e (OpenAI · MCP · OpenTelemetry)

See [`ADAPTERS-E2E.md`](./ADAPTERS-E2E.md) and runnable stubs:

```bash
python examples/e2e_openai.py
python examples/e2e_mcp.py
python examples/e2e_otel.py
```

## Cloud API

- Site: https://narna.org
- API: https://api.narna.org
- Health: `GET /v1/health`

## Publish (maintainers)

1. Create PyPI API token at https://pypi.org/manage/account/#api-tokens (`pypi-…`)
2. GitHub → Settings → Secrets → `PYPI_API_TOKEN`
3. Tag and push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Workflow: `.github/workflows/publish-pypi.yml`

Or local:

```bash
python -m build
twine upload dist/*   # TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-…
```

Until published, use `pip install -e .` from git.